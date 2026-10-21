"""Offline checks for the optional deployment-only memory log."""

import asyncio
from contextlib import asynccontextmanager, redirect_stdout
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.testclient import TestClient
from deployment.memory_log import (MAX_REQUEST_SAMPLES, MemoryLog, cgroup_directory,
                                   counter, process_peak_bytes, with_memory_log)


class MemoryLogTests(unittest.TestCase):
    def test_default_and_explicit_zero_do_not_probe_or_wrap(self):
        app = object()
        with patch("deployment.memory_log.cgroup_directory", side_effect=AssertionError("must not probe")):
            for environment in ({}, {"FDA_MEMORY_LOG": "0"}):
                self.assertIs(with_memory_log(app, "release", environment), app)

    def test_enable_is_explicit_and_linux_only(self):
        with patch("deployment.memory_log.sys.platform", "linux"), patch("deployment.memory_log.cgroup_directory"):
            self.assertIsInstance(with_memory_log(object(), "release", {"FDA_MEMORY_LOG": "1"}), MemoryLog)
        for value in ("", "true", "yes", "2", " 1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                with_memory_log(object(), "release", {"FDA_MEMORY_LOG": value})
        with patch("deployment.memory_log.sys.platform", "win32"), self.assertRaisesRegex(ValueError, "Linux"):
            with_memory_log(object(), "release", {"FDA_MEMORY_LOG": "1"})

    def test_cgroup_mapping_checks_membership_instead_of_guessing_root(self):
        for member, root, expected in (("/", "/", "/sys/fs/cgroup"),
                ("/service/fda", "/", "/sys/fs/cgroup/service/fda"),
                ("/service/fda", "/service", "/sys/fs/cgroup/fda")):
            content = {"/proc/self/cgroup": "0::" + member + "\n",
                "/proc/self/mountinfo": f"42 41 0:29 {root} /sys/fs/cgroup ro - cgroup2 cgroup rw\n",
                expected + "/cgroup.procs": str(os.getpid()) + "\n"}
            with self.subTest(member=member, root=root), patch.object(Path, "read_text", autospec=True,
                    side_effect=lambda path: content.get(path.as_posix(), "")):
                self.assertEqual(cgroup_directory().as_posix(), expected)

    def test_unmapped_or_unreadable_cgroup_stays_unknown(self):
        for member in ("/other", "/../escape", "relative"):
            content = {"/proc/self/cgroup": "0::" + member + "\n",
                "/proc/self/mountinfo": "42 41 0:29 /service /sys/fs/cgroup ro - cgroup2 cgroup rw\n"}
            with patch.object(Path, "read_text", autospec=True, side_effect=lambda path: content.get(path.as_posix(), "")):
                self.assertIsNone(cgroup_directory())
        with patch.object(Path, "read_text", side_effect=PermissionError):
            self.assertIsNone(cgroup_directory())
        with patch.object(Path, "read_text", return_value=""):
            self.assertIsNone(cgroup_directory())
        content = {"/proc/self/cgroup": "0::/\n",
            "/proc/self/mountinfo": "42 41 0:29 / /sys/fs/cgroup ro - cgroup2 cgroup rw\n",
            "/sys/fs/cgroup/cgroup.procs": "999999999\n"}
        with patch.object(Path, "read_text", autospec=True, side_effect=lambda path: content.get(path.as_posix(), "")):
            self.assertIsNone(cgroup_directory())

    def test_counters_preserve_zero_but_not_missing_unlimited_or_malformed(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for value, expected in (("0\n", 0), ("512000000\n", 512000000),
                    ("max\n", None), ("-1", None), ("bad", None), ("", None)):
                (directory / "memory.max").write_text(value)
                self.assertEqual(counter(directory, "memory.max"), expected)
            self.assertIsNone(counter(directory, "missing"))
            self.assertIsNone(counter(None, "memory.max"))

    def test_linux_process_high_water_is_converted_from_kib_to_bytes(self):
        resource = SimpleNamespace(RUSAGE_SELF=0, getrusage=Mock(return_value=SimpleNamespace(ru_maxrss=123)))
        with patch.dict(sys.modules, {"resource": resource}):
            self.assertEqual(process_peak_bytes(), 123 * 1024)
        resource.getrusage.assert_called_once_with(resource.RUSAGE_SELF)

    def test_real_lifespan_http_passthrough_privacy_and_output_cap(self):
        events = []

        @asynccontextmanager
        async def lifespan(app):
            events.append("start")
            yield
            events.append("stop")

        app = FastAPI(lifespan=lifespan)

        @app.get("/api/v1/fda/explore")
        async def explore():
            return {"unchanged": True}

        @app.get("/readyz")
        async def ready():
            return {"status": "ready"}

        output = io.StringIO()
        with patch("deployment.memory_log.cgroup_directory", return_value=None), \
                patch("deployment.memory_log.process_peak_bytes", return_value=123456), redirect_stdout(output):
            wrapped = MemoryLog(app, "checked-release")
            with TestClient(wrapped) as client:
                for _ in range(MAX_REQUEST_SAMPLES + 3):
                    response = client.get("/api/v1/fda/explore?productFilter=private-search&reportId=private-id")
                    self.assertEqual(response.json(), {"unchanged": True})
                    self.assertEqual(response.status_code, 200)
                self.assertEqual(client.get("/readyz").json(), {"status": "ready"})
        lines = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(events, ["start", "stop"])
        self.assertEqual(len(lines), MAX_REQUEST_SAMPLES + 2)
        self.assertEqual((lines[0]["phase"], lines[-1]["phase"]), ("startup", "shutdown"))
        self.assertEqual(lines[-1]["requestSamples"], MAX_REQUEST_SAMPLES)
        self.assertTrue(all(row["processPeakRssBytes"] == 123456 for row in lines))
        self.assertTrue(all(row["cgroupPeakBytes"] is None for row in lines))
        self.assertNotIn("private-search", output.getvalue())
        self.assertNotIn("private-id", output.getvalue())
        self.assertNotIn("/api/", output.getvalue())

    def test_measurement_and_stdout_failures_do_not_break_responses(self):
        with patch("deployment.memory_log.cgroup_directory", return_value=None):
            wrapped = MemoryLog(None, "release")
        output = io.StringIO()
        with patch("deployment.memory_log.process_peak_bytes", side_effect=OSError), redirect_stdout(output):
            wrapped.emit("request")
        self.assertIsNone(json.loads(output.getvalue())["processPeakRssBytes"])
        with patch("builtins.print", side_effect=BrokenPipeError):
            wrapped.emit("shutdown")


class CancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_errors_and_cancellation_are_not_swallowed_by_diagnostics(self):
        for error in (RuntimeError("original"), asyncio.CancelledError()):
            async def app(scope, receive, send):
                raise error
            with patch("deployment.memory_log.cgroup_directory", return_value=None):
                wrapped = MemoryLog(app, "release")
            with patch.object(wrapped, "emit") as emit, self.assertRaises(type(error)):
                await wrapped({"type": "http", "path": "/api/v1/fda/explore"}, None, None)
            emit.assert_called_once_with("request")


if __name__ == "__main__":
    unittest.main(verbosity=2)
