"""Opt-in, bounded Linux memory diagnostics; no request or report data."""

import json
import os
from pathlib import Path, PurePosixPath
import sys
import time


MAX_REQUEST_SAMPLES = 200


def cgroup_directory():
    try:
        member = next(line[3:] for line in Path("/proc/self/cgroup").read_text().splitlines()
                      if line.startswith("0::"))
        if not member.startswith("/") or ".." in PurePosixPath(member).parts:
            return None
        for line in Path("/proc/self/mountinfo").read_text().splitlines():
            before, separator, after = line.partition(" - ")
            fields = before.split()
            if not separator or after.split()[0] != "cgroup2" or len(fields) < 5:
                continue
            root, mount = fields[3:5]
            if "\\" in root + mount or not root.startswith("/") or not mount.startswith("/"):
                continue
            try:
                relative = PurePosixPath(member).relative_to(root)
            except ValueError:
                continue
            directory = Path(mount).joinpath(*relative.parts)
            # Never label an unrelated mount/ancestor's counters as this worker's group.
            if str(os.getpid()) in (directory / "cgroup.procs").read_text().splitlines():
                return directory
    except (OSError, ValueError, StopIteration, IndexError):
        pass
    return None


def counter(directory, name):
    if directory is None:
        return None
    try:
        value = (directory / name).read_text().strip()
        return int(value) if value.isascii() and value.isdecimal() else None
    except (OSError, ValueError):
        return None


def process_peak_bytes():
    from resource import RUSAGE_SELF, getrusage
    return getrusage(RUSAGE_SELF).ru_maxrss * 1024


class MemoryLog:
    def __init__(self, app, release_id):
        self.app = app
        self.release_id = release_id
        self.directory = cgroup_directory()
        self.started = time.monotonic()
        self.requests = 0

    def emit(self, phase):
        try:
            try:
                peak = process_peak_bytes()
            except (OSError, ValueError, ImportError):
                peak = None
            print(json.dumps({"event": "fda_memory", "phase": phase, "pid": os.getpid(),
                "releaseId": self.release_id, "requestSamples": self.requests,
                "uptimeSeconds": round(time.monotonic() - self.started, 3),
                "processPeakRssBytes": peak, "cgroupV2Resolved": self.directory is not None,
                "cgroupCurrentBytes": counter(self.directory, "memory.current"),
                "cgroupPeakBytes": counter(self.directory, "memory.peak"),
                "cgroupMaxBytes": counter(self.directory, "memory.max")}, separators=(",", ":")), flush=True)
        except Exception:
            # Diagnostics must not mask a response, cancellation or shutdown failure.
            pass

    async def __call__(self, scope, receive, send):
        if scope["type"] == "lifespan":
            async def lifespan_send(message):
                if message["type"] == "lifespan.startup.complete":
                    self.emit("startup")
                elif message["type"] == "lifespan.shutdown.complete":
                    self.emit("shutdown")
                await send(message)
            return await self.app(scope, receive, lifespan_send)
        sample = (scope["type"] == "http" and scope.get("path", "").startswith("/api/v1/fda/")
                  and self.requests < MAX_REQUEST_SAMPLES)
        if sample:
            self.requests += 1
        try:
            return await self.app(scope, receive, send)
        finally:
            if sample:
                self.emit("request")


def with_memory_log(app, release_id, environment):
    flag = environment.get("FDA_MEMORY_LOG", "0")
    if flag not in ("0", "1"):
        raise ValueError("FDA_MEMORY_LOG must be 0 or 1; it defaults to 0.")
    if flag == "0":
        return app
    if sys.platform != "linux":
        raise ValueError("FDA_MEMORY_LOG=1 is supported only by the Linux deployment launcher.")
    return MemoryLog(app, release_id)
