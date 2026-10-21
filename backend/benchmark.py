"""Real loopback HTTP parity and five-client timings; the server is a separate process."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import socket
import statistics
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from common import environment, sha256_file, write_json


def compare(actual, expected, path="result"):
    if isinstance(expected, float):
        if actual is None or not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-10):
            raise AssertionError(path)
    elif isinstance(expected, dict):
        for key, value in expected.items():
            compare(actual[key], value, path + "." + key)
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise AssertionError(path + " length")
        for index, (left, right) in enumerate(zip(actual, expected)):
            compare(left, right, f"{path}[{index}]")
    elif actual != expected:
        raise AssertionError(path)


def path_for(resource="explore", **params):
    params = {key: value for key, value in params.items() if value is not None}
    return "/api/v1/fda/" + resource + ("?" + urlencode(params) if params else "")


def request(base, path, submitted=None):
    started = submitted if submitted is not None else time.perf_counter_ns()
    try:
        with urlopen(base + path, timeout=45) as response:
            payload, status = response.read(), response.status
    except HTTPError as error:
        payload, status = error.read(), error.code
    finished = time.perf_counter_ns()
    elapsed = (finished - started) / 1e6
    try:
        value = json.loads(payload)
    except ValueError:
        value = None
    return {"status": status, "latencyMs": elapsed, "bytes": len(payload),
            "submittedNs": started, "receivedNs": finished}, value


def parity(base, oracle):
    results = {}
    for name, expected in oracle["cases"].items():
        filters = expected["filters"]
        record, value = request(base, path_for(**filters))
        if record["status"] != 200:
            raise AssertionError("HTTP overview failed: " + name)
        compare(value["overview"], expected["overview"], name)
        ids, cursor, pages = [], None, 0
        while True:
            record, value = request(base, path_for("reports", **filters, limit=100, cursor=cursor))
            if record["status"] != 200:
                raise AssertionError("HTTP page failed: " + name)
            page = value["page"]
            ids.extend(item["reportId"] for item in page["items"])
            pages += 1
            if not page["hasMore"]:
                break
            cursor = page["nextCursor"]
            if pages > 1000:
                raise AssertionError("Pagination failed to advance.")
        compare(ids, expected["selectedIds"], name + ".selectedIds")
        for rid, detail in expected["details"].items():
            record, value = request(base, path_for("reports/detail", **filters, reportId=rid))
            if record["status"] != 200:
                raise AssertionError("HTTP detail failed: " + name)
            compare(value["detail"]["report"], detail, name + ".detail")
        results[name] = {"parity": "pass", "reports": len(ids), "pages": pages,
                         "details": len(expected["details"]), "filters": filters}
        print(f"HTTP {name}: {len(ids):,} IDs, {pages} pages, detail and overview parity pass", flush=True)
    return results


def stats(records):
    latencies = sorted(item["latencyMs"] for item in records)
    successes = [item for item in records if item["status"] == 200]
    return {"requests": len(records), "successes": len(successes),
            "statuses": {str(status): sum(item["status"] == status for item in records) for status in sorted({item["status"] for item in records})},
            "allRequestLatencyMs": {"median": statistics.median(latencies), "p95": latencies[math.ceil(.95 * len(latencies)) - 1], "max": max(latencies)},
            "successfulP95Ms": sorted(item["latencyMs"] for item in successes)[math.ceil(.95 * len(successes)) - 1] if successes else None,
            "records": records}


def timings(base, rounds):
    default = path_for()
    carrot = path_for(productFilter="CARROTS")
    mixed = [carrot, path_for(productFilter="VITAMIN D3"), path_for(productFilter="%"),
             path_for(productFilter="no-match-7c46ba"), path_for(startYear=2024, endYear=2024)]
    scenarios = {"default": [default] * 5, "repeated_uncached": [carrot] * 5,
                 "mixed_uncached": mixed, "mixed_with_default": [default, mixed[0], default, mixed[2], mixed[4]]}
    results = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        for name, paths in scenarios.items():
            for path in paths:
                record, _ = request(base, path)
                if record["status"] != 200:
                    raise AssertionError("Warm-up failed")
            records = []
            for wave in range(rounds):
                futures = [pool.submit(request, base, path, time.perf_counter_ns()) for path in paths]
                for index, future in enumerate(futures):
                    record, _ = future.result()
                    records.append({**record, "wave": wave, "fixture": index,
                                    "preparedDefault": paths[index] == default})
            results[name] = stats(records)
            print(f"HTTP {name}: {results[name]['statuses']}; p95 {results[name]['allRequestLatencyMs']['p95']:.2f}ms", flush=True)
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = [pool.submit(request, base, carrot, time.perf_counter_ns()) for _ in range(20)]
        results["overload"] = stats([future.result()[0] for future in futures])
    with ThreadPoolExecutor(max_workers=5) as busy, ThreadPoolExecutor(max_workers=5) as readers:
        work = [busy.submit(request, base, carrot, time.perf_counter_ns()) for _ in range(5)]
        time.sleep(.1)
        defaults = [readers.submit(request, base, default, time.perf_counter_ns()) for _ in range(5)]
        results["default_interleaved_with_five_sql"] = stats([future.result()[0] for future in defaults])
        results["five_sql_background"] = stats([future.result()[0] for future in work])
    # Real TCP disconnect: the SQL token, not merely a client future, must be canceled.
    parsed = base.rsplit(":", 1)
    with socket.create_connection(("127.0.0.1", int(parsed[1])), timeout=5) as client:
        client.sendall((f"GET {carrot} HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n").encode("ascii"))
        time.sleep(.05)
    time.sleep(.5)
    defaults = results["default"]
    if defaults["successes"] != defaults["requests"] or defaults["successfulP95Ms"] >= 10000:
        raise AssertionError("The five-client default gate failed.")
    if any(value["successes"] != value["requests"] for key, value in results.items() if key != "overload"):
        raise AssertionError("A five-client scenario failed; do not hide it in successful-only latency.")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-directory", type=Path, required=True)
    parser.add_argument("--release-id", required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--oracle", type=Path)
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--constrained", action="store_true")
    parser.add_argument("--port", type=int, default=8876)
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("At least one measured wave is required.")
    output = args.output_directory.resolve()
    output.mkdir(parents=True, exist_ok=True)
    base = f"http://127.0.0.1:{args.port}"
    root = Path(__file__).resolve().parents[1]
    code = {path.relative_to(root).as_posix(): sha256_file(path) for path in sorted((root / "backend").rglob("*.py"))}
    database_before = sha256_file(args.release_directory / "fda.sqlite3")
    command = [sys.executable, "-u", "-B", "-m", "backend.run", "--release-directory", str(args.release_directory.resolve()),
               "--release-id", args.release_id, "--port", str(args.port), "--control-stdin", "--metrics-output", str(output / "server.json")]
    if args.constrained:
        command += ["--constrained", "--keep-awake"]
    with (output / "server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 120
            while True:
                if server.poll() is not None:
                    raise RuntimeError("Local server failed; see its saved log.")
                try:
                    record, value = request(base, "/readyz")
                    if record["status"] == 200:
                        if value["releaseId"] != args.release_id:
                            raise AssertionError("Unexpected server release")
                        break
                except (URLError, OSError):
                    pass
                if time.monotonic() > deadline:
                    raise TimeoutError("Local server did not become ready")
                time.sleep(.1)
            cases = parity(base, json.loads(args.oracle.read_bytes())) if args.oracle else None
            results = timings(base, args.rounds)
            _, schema = request(base, "/openapi.json")
            write_json(output / "openapi.json", schema)
        finally:
            server.stdin.close()
            try:
                server.wait(timeout=40)
            except subprocess.TimeoutExpired:
                server.terminate()
                server.wait(timeout=10)
    if server.returncode != 0:
        raise RuntimeError("Server shutdown failed; inspect its log before accepting measurements.")
    metrics = json.loads((output / "server.json").read_bytes())
    if metrics["heavyImports"] or metrics["peakActiveSql"] > 5 or metrics["remainingActiveSql"] != 0:
        raise AssertionError("Server resource/import ownership invariant failed")
    if any(sha256_file(root / name) != digest for name, digest in code.items()):
        raise AssertionError("Measured backend code changed during the run.")
    if sha256_file(args.release_directory / "fda.sqlite3") != database_before:
        raise AssertionError("Database changed during HTTP verification/profile.")
    write_json(output / "results.json", {"releaseId": args.release_id, "parity": cases, "scenarios": results,
        "databaseSha256": database_before,
        "server": metrics, "clientEnvironment": environment(), "codeSha256": code,
        "method": "Five clients, closed-loop waves, new loopback HTTP connection per request. Time begins before executor submission and ends after receiving the complete body; includes dispatch, server handling, SQL, validation and transfer. No browser, internet, host wake-up or unbounded arrivals."})
    print("Real HTTP verification/profile complete; server stopped and all SQL slots released.", flush=True)


if __name__ == "__main__":
    main()
