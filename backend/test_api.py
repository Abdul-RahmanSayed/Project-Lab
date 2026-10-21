"""Local contract and lifecycle regressions against a separately checked release."""

import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path
import shutil
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from common import sha256_file, write_json
from .app import create_app
from .config import Settings
from .fda.parameters import make_cursor
from .fda.repository import connection


SETTINGS = None


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app(SETTINGS)
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.assertEqual(self.client.get("/readyz").status_code, 200)

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def test_saved_default_exact_selection_and_conditional_response(self):
        first = self.client.get("/api/v1/fda/explore")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["source"], "prepared-default")
        self.assertFalse(first.json()["isLive"])
        tag = first.headers["etag"]
        for candidate in (tag, "W/" + tag, "*", '"other", ' + tag):
            self.assertEqual(self.client.get("/api/v1/fda/explore", headers={"If-None-Match": candidate}).status_code, 304)
        changed = self.client.get("/api/v1/fda/explore", params={"startYear": 2026}, headers={"If-None-Match": tag})
        self.assertEqual(changed.status_code, 200)
        self.assertEqual(changed.json()["source"], "sqlite")
        self.assertEqual(changed.json()["overview"]["selectedCount"], 24)
        self.assertNotIn("etag", changed.headers)
        self.assertEqual(self.client.get("/api/v1/fda/explore", params={"productFilter": "null"}).json()["source"], "sqlite")

    def test_invalid_parameters_and_literal_url_content(self):
        for query in ("startYear=2026&endYear=2024", "startYear=true", "startYear=2024.0",
                      "productFilter=", "productFilter=+++", "productFilter=" + "a" * 257,
                      "startYear=2024&startYear=2025", "unknown=1", "productFilter=%FF", "productFilter=%QZ"):
            with self.subTest(query=query[:50]):
                response = self.client.get("/api/v1/fda/explore?" + query)
                self.assertEqual(response.status_code, 422)
                self.assertIn("error", response.json())
        for product in ("%", "_", "+", "cArRoTs", " a ", "Stra\u00dfe"):
            response = self.client.get("/api/v1/fda/explore", params={"productFilter": product})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["overview"]["appliedFilters"]["productFilter"], product)

    def test_empty_and_missing_age_selections(self):
        response = self.client.get("/api/v1/fda/explore", params={"productFilter": "no-match-1e589f26"})
        value = response.json()["overview"]
        self.assertEqual(value["selectedCount"], 0)
        self.assertEqual(value["ageMeans"], {"total": None, "female": None, "male": None})
        self.assertEqual(len(value["ageHistogram"]), 126)
        self.assertEqual(sum(count for _, count in value["ageHistogram"]), 0)
        page = self.client.get("/api/v1/fda/reports", params={"productFilter": "no-match-1e589f26"}).json()["page"]
        self.assertEqual(page["items"], [])
        self.assertIsNone(page["nextCursor"])

    def test_paging_context_ids_detail_and_restart(self):
        params = {"productFilter": "CARROTS", "limit": 25}
        first = self.client.get("/api/v1/fda/reports", params=params).json()["page"]
        second = self.client.get("/api/v1/fda/reports", params={**params, "cursor": first["nextCursor"]}).json()["page"]
        self.assertLess(first["items"][-1]["reportId"], second["items"][0]["reportId"])
        self.assertEqual(len(first["items"]), 25)
        item = first["items"][0]
        response = self.client.get("/api/v1/fda/reports/detail", params={"productFilter": "CARROTS", "reportId": item["reportId"]})
        self.assertEqual(response.status_code, 200)
        detail = response.json()["detail"]["report"]
        self.assertEqual(detail["reportId"], item["reportId"])
        self.assertTrue(any(product["matchesProductFilter"] for product in detail["products"]))
        self.assertNotIn("rawReport", detail)
        self.assertEqual(self.client.get("/api/v1/fda/reports/detail", params={"reportId": item["reportId"], "productFilter": "no-match-1e589f26"}).status_code, 404)
        self.assertEqual(self.client.get("/api/v1/fda/reports/detail", params={"reportId": "../no-such-report"}).status_code, 404)
        self.assertEqual(self.client.get("/api/v1/fda/reports", params={**params, "limit": 100, "cursor": first["nextCursor"]}).status_code, 409)
        self.assertEqual(self.client.get("/api/v1/fda/reports", params={**params, "productFilter": "carrots", "cursor": first["nextCursor"]}).status_code, 409)
        for cursor in ("!", "A" * 2049, "eyJ2Ijp0cnVlfQ"):
            self.assertEqual(self.client.get("/api/v1/fda/reports", params={"cursor": cursor}).status_code, 400 if len(cursor) < 2049 else 422)
        with TestClient(create_app(SETTINGS)) as restarted:
            self.assertEqual(restarted.get("/api/v1/fda/reports", params={**params, "cursor": first["nextCursor"]}).json()["page"], second)
        # Unsigned bookmarks are intentionally editable, but never bypass current filters.
        cursor = make_cursor(SETTINGS.expected_release_id, self.app.state.fda.default_filters, 25, "\uffff")
        edited = self.client.get("/api/v1/fda/reports", params={"cursor": cursor})
        self.assertEqual(edited.status_code, 200)
        self.assertFalse(edited.json()["page"]["hasMore"])

    def test_readiness_release_errors_methods_and_schema(self):
        metadata = self.client.get("/api/v1/fda/metadata")
        self.assertEqual(metadata.json()["metadata"]["reportCount"], 97652)
        self.assertIn("not unique people", " ".join(metadata.json()["metadata"]["interpretationNotes"]))
        self.assertNotIn(str(SETTINGS.release_directory), metadata.text)
        changed = self.client.get("/api/v1/fda/explore", params={"releaseId": "fda-release-sha256:" + "0" * 64})
        self.assertEqual(changed.status_code, 409)
        self.assertEqual(self.client.post("/api/v1/fda/explore").status_code, 405)
        self.assertEqual(self.client.get("/not-a-route").status_code, 404)
        schema = self.client.get("/openapi.json").json()
        params = schema["paths"]["/api/v1/fda/reports"]["get"]["parameters"]
        self.assertIn("productFilter", {item["name"] for item in params})
        self.assertIn("ReportsResponse", schema["components"]["schemas"])
        self.assertEqual(changed.headers["x-request-id"], changed.json()["requestId"])
        self.assertEqual(changed.headers["cache-control"], "no-store")

    def test_overload_has_no_queue_and_default_bypasses_sql(self):
        entered, release = threading.Event(), threading.Event()
        current = self.app.state.fda
        operation = current.execute

        def held(*args, **kwargs):
            entered.set()
            release.wait(3)
            return operation(*args, **kwargs)

        try:
            with patch.object(current, "execute", side_effect=held), ThreadPoolExecutor(max_workers=5) as pool:
                futures = [pool.submit(self.client.get, "/api/v1/fda/reports", params={"limit": 1}) for _ in range(5)]
                self.assertTrue(entered.wait(2))
                deadline = time.monotonic() + 2
                while len(self.app.state.jobs.active) != 5 and time.monotonic() < deadline:
                    time.sleep(.01)
                overflow = self.client.get("/api/v1/fda/reports")
                self.assertEqual(overflow.status_code, 503)
                self.assertEqual(overflow.json()["error"]["code"], "SERVICE_BUSY")
                self.assertEqual(overflow.headers["retry-after"], "2")
                self.assertEqual(self.client.get("/api/v1/fda/explore").status_code, 200)
                self.assertEqual(self.client.get("/healthz").status_code, 200)
                self.assertEqual(self.client.get("/readyz").status_code, 200)
                release.set()
                self.assertTrue(all(future.result().status_code == 200 for future in futures))
        finally:
            release.set()
        self.assertEqual(self.app.state.jobs.peak_active, 5)


class FailureTests(unittest.TestCase):
    def test_missing_unreadable_wrong_identity_and_corrupt_releases_fail_closed(self):
        candidates = [replace(SETTINGS, release_directory=SETTINGS.release_directory / "missing"),
                      replace(SETTINGS, expected_release_id="fda-release-sha256:" + "0" * 64)]
        with tempfile.TemporaryDirectory(dir=SETTINGS.release_directory.parent.parent) as temp:
            target = Path(temp) / "corrupt"
            shutil.copytree(SETTINGS.release_directory, target)
            (target / "saved-overview.json").write_bytes(b"{}")
            candidates.append(replace(SETTINGS, release_directory=target))
            for candidate in candidates:
                with TestClient(create_app(candidate)) as client:
                    self.assertEqual(client.get("/healthz").status_code, 200)
                    self.assertEqual(client.get("/readyz").status_code, 503)
                    self.assertEqual(client.get("/api/v1/fda/explore").status_code, 503)
                    self.assertFalse(client.get("/api/v1/projects").json()["projects"][0]["ready"])
        with patch("backend.app.Service", side_effect=PermissionError("Unreadable release")):
            with TestClient(create_app(SETTINGS)) as client:
                self.assertEqual(client.get("/healthz").status_code, 200)
                self.assertEqual(client.get("/readyz").status_code, 503)
                self.assertEqual(client.get("/api/v1/fda/explore").status_code, 503)
                self.assertFalse(client.get("/api/v1/projects").json()["projects"][0]["ready"])

    def test_prepared_shape_is_validated_even_with_consistent_artifact_hashes(self):
        with tempfile.TemporaryDirectory(dir=SETTINGS.release_directory.parent.parent) as temp:
            target = Path(temp) / "shape"
            shutil.copytree(SETTINGS.release_directory, target)
            path = target / "saved-overview.json"
            payload = json.loads(path.read_bytes())
            payload["overview"]["ageHistogram"] = []
            write_json(path, payload)
            release = json.loads((target / "release.json").read_bytes())
            release["files"][path.name] = {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            write_json(target / "release.json", release)
            with TestClient(create_app(replace(SETTINGS, release_directory=target))) as client:
                self.assertEqual(client.get("/readyz").status_code, 503)
                self.assertEqual(client.get("/api/v1/fda/explore").status_code, 503)

    def test_timeout_interrupts_native_sql_and_keeps_readiness(self):
        app = create_app(replace(SETTINGS, request_seconds=.05, sql_jobs=1))
        with TestClient(app) as client:
            def heavy(kind, filters, token, **kwargs):
                with connection(app.state.fda.database, token) as db:
                    return db.execute("WITH RECURSIVE n(x) AS (VALUES(0) UNION ALL SELECT x+1 FROM n WHERE x < 1000000000) SELECT SUM(x) FROM n").fetchone()
            with patch.object(app.state.fda, "execute", side_effect=heavy):
                result = client.get("/api/v1/fda/reports")
                self.assertEqual(result.status_code, 503)
                self.assertEqual(result.json()["error"]["code"], "QUERY_TIMEOUT")
                end = time.monotonic() + 2
                while app.state.jobs.active and time.monotonic() < end:
                    time.sleep(.01)
                self.assertFalse(app.state.jobs.active)
                self.assertEqual(client.get("/readyz").status_code, 200)

    def test_timeout_does_not_release_a_stalled_worker_slot(self):
        app = create_app(replace(SETTINGS, request_seconds=.03, sql_jobs=1))
        gate = threading.Event()
        try:
            with TestClient(app) as client:
                def stalled(*args, **kwargs):
                    gate.wait(2)
                    return b"{}"
                with patch.object(app.state.fda, "execute", side_effect=stalled):
                    self.assertEqual(client.get("/api/v1/fda/reports").json()["error"]["code"], "QUERY_TIMEOUT")
                    self.assertEqual(len(app.state.jobs.active), 1)
                    self.assertEqual(client.get("/api/v1/fda/reports").json()["error"]["code"], "SERVICE_BUSY")
                    self.assertEqual(client.get("/api/v1/fda/explore").status_code, 200)
                    gate.set()
        finally:
            gate.set()

    def test_size_limit_cors_and_database_unchanged(self):
        before = sha256_file(SETTINGS.release_directory / "fda.sqlite3")
        app = create_app(replace(SETTINGS, allowed_origins=("http://localhost:5173",)))
        with TestClient(app) as client:
            response = client.get("/api/v1/fda/reports", headers={"Origin": "http://localhost:5173"})
            self.assertEqual(response.headers["access-control-allow-origin"], "http://localhost:5173")
            self.assertNotIn("access-control-allow-origin", client.get("/healthz", headers={"Origin": "http://other.invalid"}).headers)
            app.state.fda.settings = replace(app.state.fda.settings, max_response_bytes=1)
            self.assertEqual(client.get("/api/v1/fda/reports").json()["error"]["code"], "RESPONSE_TOO_LARGE")
            self.assertEqual(client.get("/api/v1/fda/explore?productFilter=" + "a" * 8200).status_code, 414)
        self.assertEqual(sha256_file(SETTINGS.release_directory / "fda.sqlite3"), before)

    def test_disconnect_signals_running_sql_and_releases_only_after_exit(self):
        async def run():
            app = create_app(SETTINGS)
            async with app.router.lifespan_context(app):
                exited = threading.Event()

                def heavy(kind, filters, token, **kwargs):
                    try:
                        with connection(app.state.fda.database, token) as db:
                            db.execute("WITH RECURSIVE n(x) AS (VALUES(0) UNION ALL SELECT x+1 FROM n WHERE x < 1000000000) SELECT SUM(x) FROM n").fetchone()
                    finally:
                        exited.set()

                began = time.monotonic()
                async def receive():
                    if time.monotonic() - began > .1:
                        return {"type": "http.disconnect"}
                    await asyncio.sleep(.2)
                    return {"type": "http.request", "body": b"", "more_body": False}
                async def send(message):
                    raise AssertionError("A disconnected client must not receive a fabricated HTTP response.")
                scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET",
                         "scheme": "http", "path": "/api/v1/fda/reports", "raw_path": b"/api/v1/fda/reports",
                         "query_string": b"", "headers": [], "client": ("127.0.0.1", 1), "server": ("127.0.0.1", 2)}
                with patch.object(app.state.fda, "execute", side_effect=heavy):
                    await app(scope, receive, send)
                    end = time.monotonic() + 2
                    while app.state.jobs.active and time.monotonic() < end:
                        await asyncio.sleep(.01)
                    self.assertTrue(exited.is_set())
                    self.assertFalse(app.state.jobs.active)
        asyncio.run(run())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-directory", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    SETTINGS = Settings(args.release_directory.resolve(), args.release_id)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__)))
    write_json(args.output, {"testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
                            "releaseId": SETTINGS.expected_release_id})
    raise SystemExit(not result.wasSuccessful())
