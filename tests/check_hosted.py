"""Bounded HTTPS checks of the approved Render API; no provisioning or keep-awake."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPException
import json
from pathlib import Path
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "data-build"))

from backend.benchmark import path_for, stats
from check_container import check_parity
from common import sha256_file, write_json

MAX_BYTES = 2 * 1024 * 1024


def api_origin(value):
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or not parsed.hostname.endswith(".onrender.com")
            or parsed.username or parsed.password or parsed.port not in (None, 443)
            or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
        raise ValueError("Use the approved plain HTTPS onrender.com origin.")
    return f"https://{parsed.hostname}"


def request(base, path, submitted=None, origin=None):
    started = submitted if submitted is not None else time.perf_counter_ns()
    headers = {"Origin": origin} if origin else {}
    response_headers, payload, status, failure = {}, b"", 0, None
    try:
        try:
            response = urlopen(Request(base + path, headers=headers), timeout=45)
        except HTTPError as error:
            response = error
        with response:
            status = response.status
            response_headers = {key.lower(): value for key, value in response.headers.items()}
            payload = response.read(MAX_BYTES + 1)
        if len(payload) > MAX_BYTES:
            raise ValueError("Response exceeds the bounded test client size.")
    except (OSError, ValueError, HTTPException) as error:
        status, failure = 0, type(error).__name__
    finished = time.perf_counter_ns()
    try:
        value = json.loads(payload) if status else None
    except ValueError:
        value = None
    record = {"status": status, "latencyMs": (finished - started) / 1e6, "bytes": len(payload),
              "submittedNs": started, "receivedNs": finished,
              "headers": {key: response_headers.get(key) for key in
                          ("access-control-allow-origin", "x-fda-release-id", "x-api-contract", "retry-after")}}
    if failure:
        record["transportError"] = failure
    if isinstance(value, dict) and "error" in value:
        record["errorCode"] = value["error"].get("code")
    return record, value


def check_metadata(actual, bundled, release_id):
    assert actual["releaseId"] == bundled["releaseId"] == release_id
    for key in ("datasetId", "policyVersion", "schemaHash", "queryHash", "sourceRevision"):
        assert actual["metadata"][key] == bundled["metadata"][key], key


def wave(pool, base, paths, release_id, number):
    pending = [pool.submit(request, base, path, time.perf_counter_ns()) for path in paths]
    records = []
    for index, future in enumerate(pending):
        record, payload = future.result()
        if record["status"] == 200:
            expected = "prepared-default" if paths[index] == path_for() else "sqlite"
            assert (payload is not None and payload.get("releaseId") == release_id
                    and payload.get("isLive") is False and payload.get("source") == expected)
        records.append({**record, "wave": number, "fixture": index})
    return records


def timings(base, release_id):
    default = path_for()
    carrot = path_for(productFilter="CARROTS")
    mixed = [carrot, path_for(productFilter="VITAMIN D3"), path_for(productFilter="%"),
             path_for(productFilter="no-match-7c46ba"), path_for(startYear=2024, endYear=2024)]
    scenarios = {"default": ([default] * 5, 10), "repeated_uncached": ([carrot] * 5, 2),
                 "mixed_uncached": (mixed, 2),
                 "mixed_with_default": ([default, mixed[0], default, mixed[2], mixed[4]], 2)}
    results = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        for name, (paths, rounds) in scenarios.items():
            records = []
            for number in range(rounds):
                records.extend(wave(pool, base, paths, release_id, number))
                time.sleep(.2)
            results[name] = stats(records)
            print(name, results[name]["statuses"], results[name]["allRequestLatencyMs"], flush=True)
    with ThreadPoolExecutor(max_workers=10) as pool:
        results["overload"] = stats(wave(pool, base, [carrot] * 10, release_id, 0))
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-origin", required=True, type=api_origin)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--oracle", type=Path, default=ROOT / "generated/backend/api-oracle.json")
    args = parser.parse_args()
    output = args.output_directory.resolve()
    if not output.is_relative_to(ROOT / "generated"):
        parser.error("Keep generated acceptance evidence under this workspace's generated directory.")
    output.mkdir(parents=True, exist_ok=False)
    lock = json.loads((ROOT / "deployment/release.lock.json").read_bytes())
    oracle = json.loads(args.oracle.read_bytes())
    bundled = json.loads((ROOT / "web/src/generated/metadata.json").read_bytes())
    release_id = lock["releaseId"]
    browser_origin = "https://abdul-rahmansayed.github.io"
    results = {"apiOrigin": args.api_origin, "releaseId": release_id,
               "oracleSha256": sha256_file(args.oracle), "startedAtUtc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               "scope": "Warm host HTTPS full-body requests; bounded representative parity, not browser rendering or idle wake."}
    try:
        record, payload = request(args.api_origin, "/readyz")
        results["readiness"] = record
        assert record["status"] == 200 and payload["releaseId"] == release_id, "API must already be ready; no wake-up polling."
        record, payload = request(args.api_origin, path_for("metadata"), origin=browser_origin)
        results["metadata"] = record
        assert record["status"] == 200 and payload["releaseId"] == release_id
        assert record["headers"]["access-control-allow-origin"] == browser_origin
        check_metadata(payload, bundled, release_id)
        record, _ = request(args.api_origin, path_for("metadata"), origin="https://example.invalid")
        results["disallowedOrigin"] = record
        assert record["status"] == 200 and record["headers"]["access-control-allow-origin"] is None
        record, payload = request(args.api_origin, path_for(releaseId="fda-release-sha256:" + "0" * 64), origin=browser_origin)
        results["versionMismatch"] = record
        assert record["status"] == 409 and payload["error"]["code"] == "RELEASE_MISMATCH"
        assert record["headers"]["access-control-allow-origin"] == browser_origin
        results["parity"] = check_parity(args.api_origin, oracle)
        results["timings"] = timings(args.api_origin, release_id)
        default = results["timings"]["default"]
        results["defaultGatePassed"] = default["successes"] == 50 and default["allRequestLatencyMs"]["p95"] < 10000
        results["fiveClientSelectionsSucceeded"] = all(value["successes"] == value["requests"]
                                                       for name, value in results["timings"].items() if name != "overload")
        assert results["defaultGatePassed"], "Five-client warm default p95 gate failed."
        assert results["fiveClientSelectionsSucceeded"], "A selection failed; failures remain in the results."
        results["passed"] = True
    except Exception as error:
        results["passed"], results["failureType"], results["failure"] = False, type(error).__name__, str(error)
    finally:
        write_json(output / "results.json", results)
    if not results["passed"]:
        raise SystemExit("Hosted checks did not pass; inspect the recorded results.")


if __name__ == "__main__":
    main()
