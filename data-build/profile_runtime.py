"""Profile prepared reuse and uncached SQL, including dispatch/scheduling wait."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import statistics
import threading
import time

from common import environment, peak_memory, sha256_file, write_json
from prepare import validate_release
from runtime import OverviewRuntime
from verify import cases


def metrics(values):
    return {"samples": len(values), "medianMs": statistics.median(values),
            "p95Ms": sorted(values)[math.ceil(.95 * len(values)) - 1], "maxMs": max(values)}


def profile(release_directory, output, rounds, clients, constrained, idle_sleep_prevented=False):
    started_at = datetime.now(timezone.utc).isoformat()
    limits = None
    if constrained:
        from windows_limits import constrain
        limits = constrain()
        print("Applied limits: " + json.dumps(limits), flush=True)
    code_before = {name: sha256_file(Path(__file__).with_name(name))
                   for name in ("runtime.py", "profile_runtime.py", "query.py", "windows_limits.py")}
    started = time.perf_counter()
    reader = OverviewRuntime(release_directory)
    startup = time.perf_counter() - started
    release_before = validate_release(release_directory)
    selections = dict(cases())
    expected = {}
    for name, filters in selections.items():
        for _ in range(3):
            payload = reader.read(filters)
        response = json.loads(payload)
        expected[name] = {"sha256": hashlib.sha256(payload).hexdigest(),
                          "selectedCount": response["overview"]["selectedCount"], "source": response["source"]}
    scenarios = {"default_repeated": ["overall"], "carrots_repeated_uncached": ["product_carrots"],
                 "mixed_uncached": [name for name in selections if name != "overall"],
                 "mixed_with_default": list(selections)}
    results = {}

    def request(name, submitted, barrier):
        barrier.wait(timeout=120)
        began = time.perf_counter_ns()
        payload = reader.read(selections[name])
        ended = time.perf_counter_ns()
        if hashlib.sha256(payload).hexdigest() != expected[name]["sha256"]:
            raise AssertionError("Request result changed: " + name)
        return {"case": name, "responseSource": expected[name]["source"],
                "latencyMs": (ended - submitted) / 1e6, "queueWaitMs": (began - submitted) / 1e6,
                "serviceMs": (ended - began) / 1e6}

    with ThreadPoolExecutor(max_workers=clients) as pool:
        for scenario, names in scenarios.items():
            records = []
            for iteration in range(rounds):
                barrier = threading.Barrier(clients)
                futures = []
                for client in range(clients):
                    name = names[(iteration * clients + client) % len(names)]
                    submitted = time.perf_counter_ns()
                    futures.append(pool.submit(request, name, submitted, barrier))
                records.extend(future.result() for future in futures)
                if (iteration + 1) % 5 == 0:
                    print(f"{scenario}: completed {iteration + 1}/{rounds} waves", flush=True)
            by_case = {name: metrics([r["latencyMs"] for r in records if r["case"] == name])
                       for name in names if any(r["case"] == name for r in records)}
            results[scenario] = {"requestLatency": metrics([r["latencyMs"] for r in records]),
                                 "queueWait": metrics([r["queueWaitMs"] for r in records]),
                                 "serviceTime": metrics([r["serviceMs"] for r in records]),
                                 "byCase": by_case, "records": records}
            print(f"{scenario}: {len(records)} requests; p95 {results[scenario]['requestLatency']['p95Ms']:.2f}ms "
                  f"(wait included)", flush=True)
    if validate_release(release_directory) != release_before or any(
            sha256_file(Path(__file__).with_name(name)) != digest for name, digest in code_before.items()):
        raise AssertionError("Release or runtime code changed during profiling.")
    eligible = constrained and clients == 5
    measured = results["default_repeated"]["requestLatency"]["p95Ms"]
    result = {"environment": environment(), "limits": limits, "startupSeconds": startup,
              "startedAtUtc": started_at, "finishedAtUtc": datetime.now(timezone.utc).isoformat(),
              "idleSleepPreventionRequested": idle_sleep_prevented,
              "runtime": reader.describe(), "codeHashes": code_before, "clients": clients, "rounds": rounds,
              "workloads": results, "memory": peak_memory(),
              "defaultGate": {"targetP95Ms": 10000, "strictComparison": "<", "measuredP95Ms": measured,
                              "status": ("pass" if measured < 10000 else "fail") if eligible else "diagnostic-only"},
              "audit": {"releaseArtifactsUnchanged": True, "codeUnchangedDuringMeasurement": True,
                        "allResponsesMatchPreflight": True},
              "method": "3 preflight warmups per selection; synchronous 5-request waves; submission-to-byte-response timing; "
                        "wait includes executor dispatch, barrier synchronization and scheduling; SQL opens/closes a read-only "
                        "connection per request; one prepared payload; no filtered cache, eviction, semaphore, HTTP or rendering"}
    write_json(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=20)
    parser.add_argument("--clients", type=int, default=5)
    parser.add_argument("--constrained", action="store_true")
    parser.add_argument("--keep-awake", action="store_true", help="Request temporary system/display activity; restore on exit.")
    args = parser.parse_args()
    if args.rounds < 5 or not 1 <= args.clients <= 5:
        parser.error("Use at least five rounds and one to five clients.")
    if args.keep_awake:
        from windows_limits import prevent_idle_sleep
        with prevent_idle_sleep():
            profile(args.release_directory.resolve(), args.output.resolve(), args.rounds, args.clients,
                    args.constrained, idle_sleep_prevented=True)
    else:
        profile(args.release_directory.resolve(), args.output.resolve(), args.rounds, args.clients, args.constrained)
