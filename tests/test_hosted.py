"""Offline regressions for the bounded hosted-check client; no internet requests."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import io
import json
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

import check_hosted as hosted


class HostedClientTests(unittest.TestCase):
    def response(self, payload):
        result = io.BytesIO(json.dumps(payload).encode())
        result.status = 200
        result.headers = {"X-FDA-Release-ID": "checked"}
        return result

    def test_origin_requires_plain_https_render_address(self):
        self.assertEqual(hosted.api_origin("https://demo.onrender.com/"), "https://demo.onrender.com")
        for value in ("http://demo.onrender.com", "https://example.com", "https://demo.onrender.com/path",
                      "https://user:password@demo.onrender.com", "https://demo.onrender.com?token=x",
                      "https://demo.onrender.com:8765", "https://demo.onrender.com/#x"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                hosted.api_origin(value)

    def test_success_retains_headers_and_full_body(self):
        with patch.object(hosted, "urlopen", return_value=self.response({"ok": True})) as open_request:
            record, payload = hosted.request("https://demo.onrender.com", "/readyz", origin="https://example.com")
        self.assertEqual((record["status"], payload), (200, {"ok": True}))
        self.assertEqual(record["headers"]["x-fda-release-id"], "checked")
        self.assertEqual(open_request.call_args.args[0].headers["Origin"], "https://example.com")
        self.assertEqual(open_request.call_args.kwargs["timeout"], 45)

    def test_busy_response_is_not_a_success(self):
        body = io.BytesIO(b'{"error":{"code":"SERVICE_BUSY"}}')
        error = HTTPError("https://demo.onrender.com", 503, "busy", {"Retry-After": "2"}, body)
        with patch.object(hosted, "urlopen", side_effect=error):
            record, _ = hosted.request("https://demo.onrender.com", "/api/v1/fda/explore")
        self.assertEqual((record["status"], record["errorCode"]), (503, "SERVICE_BUSY"))
        self.assertEqual(record["headers"]["retry-after"], "2")

    def test_transport_failure_and_dispatch_wait_are_retained(self):
        submitted = time.perf_counter_ns() - 10_000_000
        with patch.object(hosted, "urlopen", side_effect=URLError("offline")):
            record, payload = hosted.request("https://demo.onrender.com", "/readyz", submitted)
        self.assertEqual(record["status"], 0)
        self.assertEqual(record["transportError"], "URLError")
        self.assertGreaterEqual(record["latencyMs"], 10)
        self.assertIsNone(payload)

    def test_read_is_bounded(self):
        with patch.object(hosted, "MAX_BYTES", 4), patch.object(hosted, "urlopen", return_value=self.response({"long": True})):
            record, payload = hosted.request("https://demo.onrender.com", "/readyz")
        self.assertEqual((record["status"], record["bytes"]), (0, 5))
        self.assertIsNone(payload)

    def test_changed_selection_cannot_accept_a_prepared_default(self):
        payload = {"releaseId": "checked", "isLive": False, "source": "prepared-default"}
        with patch.object(hosted, "request", return_value=({"status": 200}, payload)), ThreadPoolExecutor(max_workers=1) as pool:
            with self.assertRaises(AssertionError):
                hosted.wave(pool, "https://demo.onrender.com", [hosted.path_for(productFilter="CARROTS")], "checked", 0)

    def test_metadata_identity_uses_the_checked_frontend_bundle(self):
        bundled = {"releaseId": "checked", "metadata": {key: key + "-pin" for key in
                   ("datasetId", "policyVersion", "schemaHash", "queryHash", "sourceRevision")}}
        hosted.check_metadata(deepcopy(bundled), bundled, "checked")
        for key in bundled["metadata"]:
            wrong = deepcopy(bundled)
            wrong["metadata"][key] = "different"
            with self.subTest(key=key), self.assertRaises(AssertionError):
                hosted.check_metadata(wrong, bundled, "checked")

    def test_statistics_include_failures_and_separate_p95_from_maximum(self):
        records = [{"status": 200 if value != 20 else 0, "latencyMs": value} for value in range(1, 21)]
        result = hosted.stats(records)
        self.assertEqual((result["requests"], result["successes"]), (20, 19))
        self.assertEqual((result["allRequestLatencyMs"]["p95"], result["allRequestLatencyMs"]["max"]), (19, 20))
        self.assertEqual(result["statuses"]["0"], 1)


if __name__ == "__main__":
    unittest.main()
