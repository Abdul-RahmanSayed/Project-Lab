"""Local packaging/configuration checks, not Linux or hosted acceptance."""

import argparse
from copy import deepcopy
from contextlib import closing
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from urllib.request import Request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common import sha256_file
from deployment.release import (FILES, ReleaseRedirects, approved_url, extract_release,
                                fetch_release, pack_release, read_lock, verify_directory, write_json)
from deployment.serve import origins, settings_from_environment
from backend.app import create_app
from fastapi.testclient import TestClient


SOURCE = None
LOCK = None


class DeploymentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="fda-deployment-tests-")
        cls.root = Path(cls.temporary.name)
        cls.first = pack_release(SOURCE, LOCK["releaseId"], cls.root / "a")
        cls.second = pack_release(SOURCE, LOCK["releaseId"], cls.root / "b")
        cls.archive = cls.root / "a" / LOCK["archive"]["name"]

    @classmethod
    def tearDownClass(cls):
        for path in cls.root.rglob("*"):
            if path.is_file():
                path.chmod(0o600)
        cls.temporary.cleanup()

    def test_archive_reproduces_the_reviewed_pin_and_has_fixed_headers(self):
        self.assertEqual(self.first, LOCK)
        self.assertEqual(self.second, LOCK)
        with tarfile.open(self.archive) as bundle:
            self.assertEqual(bundle.getnames(), list(FILES))
            for member in bundle:
                self.assertTrue(member.isreg())
                self.assertEqual((member.uid, member.gid, member.mtime, member.mode), (0, 0, 0, 0o444))

    def test_roundtrip_default_filtered_and_read_only_database(self):
        destination = extract_release(self.archive, LOCK, self.root / "roundtrip")
        reader = verify_directory(destination, LOCK)
        default = json.loads(reader.read(reader.default_filters))
        self.assertEqual(default["overview"]["selectedCount"], 97652)
        filters = {**reader.default_filters, "startYear": 2024, "productFilter": "CARROTS"}
        result = json.loads(reader.read(filters))["overview"]
        self.assertEqual((result["selectedCount"], result["validAgeCount"], result["missingAgeCount"]), (149, 123, 26))
        self.assertEqual(result["yearCounts"], [[2024, 122], [2025, 27], [2026, 0]])
        from query import open_database
        with closing(open_database(destination / "fda.sqlite3")) as db:
            with self.assertRaisesRegex(Exception, "readonly"):
                db.execute("DELETE FROM reports")
        self.assertEqual(sha256_file(destination / "fda.sqlite3"), LOCK["files"]["fda.sqlite3"]["sha256"])

    def test_archive_tampering_is_rejected_before_creating_a_destination(self):
        path = self.root / "tampered.tar.gz"
        path.write_bytes(b"tampered")
        destination = self.root / "tampered-output"
        with self.assertRaisesRegex(ValueError, "Archive differs"):
            extract_release(path, LOCK, destination)
        self.assertFalse(destination.exists())

    def test_existing_output_is_never_overwritten(self):
        destination = self.root / "existing"
        destination.mkdir()
        (destination / "keep.txt").write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            extract_release(self.archive, LOCK, destination)
        self.assertEqual((destination / "keep.txt").read_text(), "keep")

    def test_wrong_release_and_changed_installed_bytes_fail_closed(self):
        wrong = deepcopy(LOCK)
        wrong["releaseId"] = "fda-release-sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "identity differs"):
            extract_release(self.archive, wrong, self.root / "wrong-release")
        self.assertFalse((self.root / "wrong-release").exists())
        destination = extract_release(self.archive, LOCK, self.root / "changed")
        path = destination / "saved-overview.json"
        path.chmod(0o600)
        path.write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "Installed release bytes differ"):
            verify_directory(destination, LOCK)

    def test_unsafe_archive_members_are_rejected_without_escape(self):
        for index, (name, kind) in enumerate([("../escape", tarfile.REGTYPE), ("/escape", tarfile.REGTYPE),
                ("extra.txt", tarfile.REGTYPE), ("fda.sqlite3", tarfile.SYMTYPE),
                ("fda.sqlite3", tarfile.LNKTYPE), ("fda.sqlite3", tarfile.DIRTYPE)]):
            with self.subTest(name=name, kind=kind):
                archive = self.root / f"unsafe-{index}.tar.gz"
                with tarfile.open(archive, "w:gz") as bundle:
                    member = tarfile.TarInfo(name)
                    member.type, member.linkname = kind, "../escape"
                    member.size = 1 if kind == tarfile.REGTYPE else 0
                    bundle.addfile(member, io.BytesIO(b"x") if kind == tarfile.REGTYPE else None)
                lock = deepcopy(LOCK)
                lock["archive"].update(bytes=archive.stat().st_size, sha256=sha256_file(archive))
                destination = self.root / f"unsafe-output-{index}"
                with self.assertRaisesRegex(ValueError, "Unsafe, duplicate or unexpected"):
                    extract_release(archive, lock, destination)
                self.assertFalse(destination.exists())
        self.assertFalse((self.root / "escape").exists())

    def test_missing_duplicate_and_wrong_size_members_are_rejected(self):
        for case in ("missing", "duplicate", "wrong-size"):
            with self.subTest(case=case):
                archive = self.root / f"{case}.tar.gz"
                with tarfile.open(archive, "w:gz") as bundle:
                    if case != "missing":
                        content = (SOURCE / "release.json").read_bytes()
                        for _ in range(2 if case == "duplicate" else 1):
                            member = tarfile.TarInfo("release.json")
                            member.size = len(content) + (1 if case == "wrong-size" else 0)
                            bundle.addfile(member, io.BytesIO(content + b"x"))
                lock = deepcopy(LOCK)
                lock["archive"].update(bytes=archive.stat().st_size, sha256=sha256_file(archive))
                with self.assertRaises(ValueError):
                    extract_release(archive, lock, self.root / f"{case}-output")

    def test_lock_bounds_and_file_inventory_are_checked(self):
        for case in ("boolean", "oversized", "missing-file", "bad-hash"):
            lock = deepcopy(LOCK)
            if case == "boolean":
                lock["archive"]["bytes"] = True
            elif case == "oversized":
                lock["archive"]["bytes"] = 1024 ** 3
            elif case == "missing-file":
                del lock["files"]["metadata.json"]
            else:
                lock["archive"]["sha256"] = "not-a-hash"
            path = self.root / f"{case}.json"
            write_json(path, lock)
            with self.subTest(case=case), self.assertRaises(ValueError):
                read_lock(path)

    def test_only_the_fixed_public_asset_url_is_accepted(self):
        url = "https://github.com/Abdul-RahmanSayed/Project-Lab/releases/download/snapshot-184460/" + LOCK["archive"]["name"]
        self.assertEqual(approved_url(url, LOCK), url)
        for candidate in (url.replace("https:", "http:"), url + "?token=secret", url + "#x",
                url.replace("snapshot-184460", "latest"), url.replace("Project-Lab", "other"),
                url.replace("github.com", "github.com.evil.invalid")):
            with self.subTest(candidate=candidate), self.assertRaises(ValueError):
                approved_url(candidate, LOCK)
        redirect = ReleaseRedirects()
        request = Request(url)
        self.assertIsNotNone(redirect.redirect_request(request, None, 302, "Found", {}, "https://release-assets.githubusercontent.com/asset?signature=example"))
        for candidate in ("http://github.com/asset", "https://evil.invalid/asset", "https://u:p@github.com/asset"):
            with self.assertRaises(ValueError):
                redirect.redirect_request(request, None, 302, "Found", {}, candidate)

    def test_production_settings_preserve_limits_and_reject_invalid_origins(self):
        environment = {"FDA_RELEASE_DIRECTORY": str(SOURCE), "FDA_ALLOWED_ORIGINS": "https://abdul-rahmansayed.github.io", "PORT": "10000"}
        settings, port = settings_from_environment(LOCK, environment)
        self.assertEqual((port, settings.sql_jobs, settings.request_seconds, settings.max_response_bytes), (10000, 5, 30, 1024 * 1024))
        for value in ("", "*", "http://example.com", "https://u:p@example.com", "https://example.com/path", "https://example.com/", "https://example.com?x=1", " https://example.com", "https://EXAMPLE.COM"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                origins(value)
        for value in ("0", "65536", "1.0", "-1", "true"):
            with self.assertRaises(ValueError):
                settings_from_environment(LOCK, {**environment, "PORT": value})
        with self.assertRaises(ValueError):
            settings_from_environment(LOCK, {**environment, "FDA_RELEASE_ID": "wrong"})

    def test_download_stream_is_bounded_and_validates_bytes_without_real_publication(self):
        url = "https://github.com/Abdul-RahmanSayed/Project-Lab/releases/download/snapshot-184460/" + LOCK["archive"]["name"]
        with self.archive.open("rb") as response, patch("deployment.release.build_opener") as opener:
            opener.return_value.open.return_value = response
            destination = fetch_release(url, LOCK, self.root / "mock-download")
            self.assertEqual(sha256_file(destination / "fda.sqlite3"), LOCK["files"]["fda.sqlite3"]["sha256"])
            self.assertEqual(opener.return_value.open.call_args.kwargs, {"timeout": 30})
        limited = deepcopy(LOCK)
        limited["archive"]["bytes"] = 1
        with patch("deployment.release.build_opener") as opener:
            opener.return_value.open.return_value = io.BytesIO(b"too much")
            with self.assertRaisesRegex(ValueError, "Download exceeded"):
                fetch_release(url, limited, self.root / "oversized-download")

    def test_actual_cors_headers_readiness_and_release_rejection(self):
        settings, _ = settings_from_environment(LOCK, {"FDA_RELEASE_DIRECTORY": str(SOURCE), "FDA_ALLOWED_ORIGINS": "https://abdul-rahmansayed.github.io"})
        with TestClient(create_app(settings)) as client:
            origin = {"Origin": "https://abdul-rahmansayed.github.io"}
            response = client.get("/api/v1/fda/metadata", headers=origin)
            self.assertEqual(response.headers["access-control-allow-origin"], origin["Origin"])
            self.assertNotIn("access-control-allow-credentials", response.headers)
            self.assertNotIn("access-control-allow-origin", client.get("/api/v1/fda/metadata", headers={"Origin": "https://other.invalid"}).headers)
            wrong = client.get("/api/v1/fda/explore?releaseId=fda-release-sha256:" + "0" * 64, headers=origin)
            self.assertEqual(wrong.status_code, 409)
            self.assertEqual(wrong.headers["access-control-allow-origin"], origin["Origin"])
            self.assertEqual(client.get("/readyz").status_code, 200)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    SOURCE = args.release_directory.resolve()
    LOCK = read_lock(Path(__file__).resolve().parents[1] / "deployment/release.lock.json")
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(DeploymentTests))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, {"testsRun": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "releaseId": LOCK["releaseId"]})
    raise SystemExit(not result.wasSuccessful())
