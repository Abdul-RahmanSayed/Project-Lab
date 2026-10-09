"""Local build, provenance, and measurement helpers."""

import ctypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys


LAB_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 2


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=True, allow_nan=False) + "\n",
                    encoding="utf-8")


def sha256_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_policy(source_repo):
    # CLI import is used only by development verification, never preparation/runtime.
    sys.dont_write_bytecode = True
    cache = LAB_ROOT / "generated" / "matplotlib-cache"
    cache.mkdir(parents=True, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = str(cache)
    spec = importlib.util.spec_from_file_location("fda_cli_oracle", Path(source_repo) / "part2.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_core():
    import fda_core
    return fda_core


def core_files(source_repo):
    root = Path(source_repo)
    names = ["pyproject.toml", "part1.js", "part2.py", "requirements.txt"]
    names += [str(path.relative_to(root)).replace("\\", "/")
              for path in sorted((root / "fda_core").glob("*.py"))]
    return {name: sha256_file(root / name) for name in names}


def content_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def source_identity(source_repo):
    source_repo = Path(source_repo).resolve()
    git = ["git", "-c", "safe.directory=" + source_repo.as_posix(), "-C", str(source_repo)]
    revision = subprocess.check_output([*git, "rev-parse", "HEAD"],
                                       text=True).strip()
    dirty = subprocess.check_output(
        [*git, "diff", "HEAD", "--name-only", "--",
         "part1.js", "part2.py", "requirements.txt", "pyproject.toml", "fda_core"], text=True).splitlines()
    return {"revision": revision, "modifiedPolicyFiles": dirty,
            "revisionKind": "local-working-tree" if dirty else "commit-plus-content-hashes",
            "files": core_files(source_repo)}


def peak_memory():
    if sys.platform == "win32":
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in (
                    "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage",
                    "PagefileUsage", "PeakPagefileUsage")]

        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return {"peakResidentBytes": counters.PeakWorkingSetSize,
                "method": "Windows GetProcessMemoryInfo PeakWorkingSetSize"}
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {"peakResidentBytes": peak if sys.platform == "darwin" else peak * 1024,
            "method": "resource.getrusage(RUSAGE_SELF).ru_maxrss"}


def environment():
    import sqlite3
    return {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version,
            "platform": platform.platform(), "machine": platform.machine(),
            "logicalCpuCount": os.cpu_count()}
