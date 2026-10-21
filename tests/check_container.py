"""Bounded local Linux/HTTP checks; never publish, provision, or rebuild data."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
import uuid
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data-build"))

from backend.benchmark import compare, path_for, request, stats
from common import sha256_file, write_json


PROBE = r'''
import hashlib, importlib.metadata, json, os, pathlib, platform, sqlite3, ssl, subprocess
root = pathlib.Path('/opt/fda/release')
def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()
def counter(name):
    path = pathlib.Path('/sys/fs/cgroup') / name
    return path.read_text() if path.exists() else None
db = sqlite3.connect('file:/opt/fda/release/fda.sqlite3?mode=ro', uri=True)
try:
    db.execute('CREATE TABLE slice5_must_not_write (value TEXT)')
except sqlite3.OperationalError as error:
    assert 'readonly' in str(error).lower(), str(error)
else:
    raise AssertionError('Database accepted a write')
finally:
    db.close()
import query
distribution = importlib.metadata.distribution('project-lab-api')
sources = {}
for member in distribution.files:
    if member.suffix != '.py':
        continue
    if member.parts[0] in ('backend', 'deployment'):
        name = str(member)
    elif len(member.parts) == 1:
        name = 'data-build/' + str(member)
    else:
        continue
    sources[name] = digest(distribution.locate_file(member))
packaging = {}
for executable in ('/opt/venv/bin/python', '/usr/local/bin/python'):
    code = "import importlib.util,json; print(json.dumps({name:importlib.util.find_spec(name) is not None for name in ('pip','setuptools')}))"
    packaging[executable] = json.loads(subprocess.check_output([executable, '-I', '-B', '-c', code], text=True))
print(json.dumps({
    'uid': os.getuid(), 'python': platform.python_version(), 'sqlite': sqlite3.sqlite_version,
    'openssl': ssl.OPENSSL_VERSION, 'packagingToolsImportable': packaging, 'sourceSha256': sources,
    'osPackages': subprocess.check_output(['dpkg-query', '-W'], text=True),
    'dependencies': {name: importlib.metadata.version(name) for name in ('fastapi', 'starlette', 'pydantic', 'uvicorn')},
    'databaseSha256': digest(root / 'fda.sqlite3'),
    'querySha256': digest(pathlib.Path(query.__file__)),
    'releaseFilesWritable': {p.name: os.access(p, os.W_OK) for p in root.iterdir()},
    'releaseFileModes': {p.name: oct(p.stat().st_mode & 0o777) for p in root.iterdir()},
    'serverProcStatus': pathlib.Path('/proc/1/status').read_text(),
    'cgroup': {name: counter(name) for name in ('memory.peak', 'memory.current', 'memory.max', 'memory.events', 'cpu.max', 'cpu.stat')}
}))
'''


def docker(*arguments, timeout=120):
    result = subprocess.run(["docker", *map(str, arguments)], capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout.strip()


def ready(base):
    started = time.perf_counter()
    deadline = started + 120
    while time.perf_counter() < deadline:
        try:
            with urlopen(base + "/readyz", timeout=3) as response:
                value = json.load(response)
                if response.status == 200:
                    return (time.perf_counter() - started) * 1000, value
        except OSError:
            pass
        time.sleep(.25)
    raise TimeoutError("Container did not become ready within 120 seconds")


def check_parity(base, oracle):
    names = ["overall", "year_2024", "product_carrots", "year_product_carrots", "empty_selection",
             "literal_percent", "literal_underscore", "partial_2026", "literal_plus", "unicode_casefold", "sample_3"]
    results = {}
    for name in names:
        expected = oracle["cases"][name]
        filters = expected["filters"]
        record, payload = request(base, path_for(**filters))
        assert record["status"] == 200, (name, record)
        compare(payload["overview"], expected["overview"], name)
        assert payload["source"] == ("prepared-default" if name == "overall" else "sqlite")
        ids, cursor, pages = [], None, 0
        # Bound local CPU work: exhaust small fixtures, inspect the first page of large ones.
        complete = len(expected["selectedIds"]) <= 300
        while True:
            record, payload = request(base, path_for("reports", **filters, limit=100, cursor=cursor))
            assert record["status"] == 200, (name, record)
            page = payload["page"]
            ids.extend(row["reportId"] for row in page["items"])
            pages += 1
            if not complete or not page["hasMore"]:
                break
            cursor = page["nextCursor"]
            assert pages <= 3
        compare(ids, expected["selectedIds"] if complete else expected["selectedIds"][:100], name + ".ids")
        for report_id, detail in list(expected["details"].items())[:1]:
            record, payload = request(base, path_for("reports/detail", **filters, reportId=report_id))
            assert record["status"] == 200, (name, record)
            compare(payload["detail"]["report"], detail, name + ".detail")
        results[name] = {"overview": "pass", "reports": len(expected["selectedIds"]), "checkedIds": len(ids),
                         "completePagination": complete, "pages": pages, "details": min(1, len(expected["details"]))}
        print("Linux HTTP parity:", name, results[name], flush=True)
    return results


def measured_wave(pool, base, paths, wave):
    pending = [pool.submit(request, base, path, time.perf_counter_ns()) for path in paths]
    records = []
    for index, future in enumerate(pending):
        record, payload = future.result()
        if record["status"] == 200:
            assert payload["isLive"] is False
            assert payload["source"] == ("prepared-default" if paths[index] == path_for() else "sqlite")
        records.append({**record, "wave": wave, "fixture": index,
                        "errorCode": payload.get("error", {}).get("code") if payload else None})
    return records


def timings(base, rounds, uncached_rounds):
    default, carrot = path_for(), path_for(productFilter="CARROTS")
    mixed = [carrot, path_for(productFilter="VITAMIN D3"), path_for(productFilter="%"),
             path_for(productFilter="no-match-7c46ba"), path_for(startYear=2024, endYear=2024)]
    scenarios = {"default": ([default] * 5, rounds), "repeated_uncached": ([carrot] * 5, uncached_rounds),
                 "mixed_uncached": (mixed, uncached_rounds),
                 "mixed_with_default": ([default, mixed[0], default, mixed[2], mixed[4]], uncached_rounds)}
    results = {}
    request(base, default)
    with ThreadPoolExecutor(max_workers=5) as pool:
        for name, (paths, count) in scenarios.items():
            records = []
            for wave in range(count):
                records.extend(measured_wave(pool, base, paths, wave))
                time.sleep(.2)
            results[name] = stats(records)
            print("Linux HTTP timings:", name, results[name]["statuses"], results[name]["allRequestLatencyMs"], flush=True)
    with ThreadPoolExecutor(max_workers=10) as pool:
        results["overload"] = stats(measured_wave(pool, base, [carrot] * 10, 0))
    time.sleep(.5)
    with ThreadPoolExecutor(max_workers=5) as busy, ThreadPoolExecutor(max_workers=5) as readers:
        work = [busy.submit(request, base, carrot, time.perf_counter_ns()) for _ in range(5)]
        time.sleep(.1)
        results["default_interleaved_with_sql"] = stats(measured_wave(readers, base, [default] * 5, 0))
        results["background_sql"] = stats([future.result()[0] for future in work])
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--oracle", type=Path, default=ROOT / "generated/backend/api-oracle.json")
    parser.add_argument("--port", type=int, default=8768)
    parser.add_argument("--rounds", type=int, default=10)
    parser.add_argument("--uncached-rounds", type=int, default=2)
    parser.add_argument("--memory-log", action="store_true", help="Enable the bounded Linux deployment memory log")
    args = parser.parse_args()
    if not 1 <= args.rounds <= 10 or not 1 <= args.uncached_rounds <= 2:
        parser.error("At most ten default waves and two waves per uncached fixture")
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=False)
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", args.port))
    base = f"http://127.0.0.1:{args.port}"
    lock = json.loads((ROOT / "deployment/release.lock.json").read_bytes())
    oracle = json.loads(args.oracle.read_bytes())
    results = {"image": json.loads(docker("image", "inspect", args.image))[0], "oracleSha256": sha256_file(args.oracle),
               "memoryLogEnabled": args.memory_log,
               "method": "Docker Desktop/WSL2 Linux/amd64, 0.1 CPU quota, 512000000-byte RAM/no swap, read-only root and non-root user. Host loopback HTTP full bodies; timing starts before executor submission. Closed-loop waves, not growing queues or hosted/network/wake evidence. No general filtered cache or evictions; the unchanged exact prepared default is reused."}
    container = None
    try:
        container = docker("create", "--pull=never", "--name", "project-lab-local-check-" + uuid.uuid4().hex[:10],
                           "--cpus", ".1", "--memory", "512000000", "--memory-swap", "512000000", "--pids-limit", "64",
                           "--read-only", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
                           "--publish", f"127.0.0.1:{args.port}:10000",
                           *(["--env", "FDA_MEMORY_LOG=1"] if args.memory_log else []), args.image)
        results["containerId"] = container
        started = time.perf_counter()
        docker("start", container)
        _, value = ready(base)
        results["startToReadyMs"] = (time.perf_counter() - started) * 1000
        assert value["releaseId"] == lock["releaseId"]
        before = json.loads(docker("exec", container, "python", "-c", PROBE))
        assert before["uid"] == 10001
        assert not any(found for interpreter in before["packagingToolsImportable"].values() for found in interpreter.values())
        for name, digest in before["sourceSha256"].items():
            assert sha256_file(ROOT / name) == digest, "Installed source differs: " + name
        assert not any(before["releaseFilesWritable"].values())
        assert before["databaseSha256"] == lock["files"]["fda.sqlite3"]["sha256"]
        assert before["querySha256"] == sha256_file(ROOT / "data-build/query.py")
        results["before"] = before
        results["parity"] = check_parity(base, oracle)
        wrong, _ = request(base, path_for(releaseId="fda-release-sha256:" + "0" * 64))
        assert wrong["status"] == 409
        results["timings"] = timings(base, args.rounds, args.uncached_rounds)
        with socket.create_connection(("127.0.0.1", args.port), timeout=5) as client:
            path = path_for(productFilter="CARROTS")
            client.sendall(f"GET {path} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n".encode("ascii"))
            time.sleep(.05)
        time.sleep(1)
        results["after"] = json.loads(docker("exec", container, "python", "-c", PROBE))
        assert results["after"]["databaseSha256"] == before["databaseSha256"]
        assert results["after"]["sourceSha256"] == before["sourceSha256"]
        default = results["timings"]["default"]
        results["warmDefaultGate"] = default["successes"] == default["requests"] and default["successfulP95Ms"] < 10000
        docker("stop", "--time", "10", container)
        results["stoppedState"] = json.loads(docker("inspect", container))[0]["State"]
        assert not results["stoppedState"]["OOMKilled"]
        docker("start", container)
        results["restartToReadyMs"], _ = ready(base)
        record, payload = request(base, path_for())
        assert record["status"] == 200 and payload["overview"]["selectedCount"] == 97652
        results["restartDefault"] = "pass"
        assert results["warmDefaultGate"], "Five-client default p95 gate failed"
        results["result"] = "pass"
    except BaseException as error:
        results["error"] = str(error)
        raise
    finally:
        if container:
            try:
                docker("stop", "--time", "10", container)
                (output / "container.log").write_text(docker("logs", container), encoding="utf-8")
                results["finalState"] = json.loads(docker("inspect", container))[0]["State"]
            finally:
                docker("rm", "--force", container)
        write_json(output / "results.json", results)
    print("Local container checks complete; owned container removed. Results:", output, flush=True)


if __name__ == "__main__":
    main()
