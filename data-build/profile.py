"""Measure sequential and five-client SQLite requests, optionally under real OS resource limits."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import statistics
import threading
import time

from common import environment, peak_memory, sha256_file, write_json
from query import explore, open_database, read_metadata


CASES = {"overall": (2002, 2026, None), "year_2024": (2024, 2024, None),
         "product_carrots": (2002, 2026, "CARROTS"), "empty": (2002, 2026, "slice1-no-such-product-9c812b")}


def metrics(samples):
    return {"samples": len(samples), "medianMs": statistics.median(samples),
            "p95Ms": sorted(samples)[math.ceil(.95 * len(samples)) - 1], "maxMs": max(samples)}


def measure(connection, filters):
    started = time.perf_counter_ns()
    result = explore(connection, filters)
    json.dumps(result, ensure_ascii=True, allow_nan=False, separators=(",", ":"))
    return (time.perf_counter_ns() - started) / 1e6, result["selectedCount"]


def profile(database, output, constrained, iterations, clients):
    limits = None
    if constrained:
        from windows_limits import constrain
        limits = constrain()
        print("Applied limits: " + json.dumps(limits), flush=True)
    sequential, concurrent = {}, {}
    connection = open_database(database)
    metadata = read_metadata(connection)
    try:
        for name, (start, end, product) in CASES.items():
            filters = {"startYear": start, "endYear": end, "productFilter": product}
            for _ in range(3):
                measure(connection, filters)
            samples = [measure(connection, filters)[0] for _ in range(iterations)]
            sequential[name] = metrics(samples)
            print(f"Sequential {name}: p95 {sequential[name]['p95Ms']:.2f}ms", flush=True)
    finally:
        connection.close()
    for name, (start, end, product) in CASES.items():
        filters = {"startYear": start, "endYear": end, "productFilter": product}
        barrier = threading.Barrier(clients)

        def client():
            connection = open_database(database)
            try:
                for _ in range(3):
                    measure(connection, filters)
                barrier.wait(timeout=120)
                return [measure(connection, filters)[0] for _ in range(iterations)]
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=clients) as pool:
            samples = [duration for group in pool.map(lambda _: client(), range(clients)) for duration in group]
        concurrent[name] = metrics(samples)
        print(f"{clients} clients {name}: p95 {concurrent[name]['p95Ms']:.2f}ms", flush=True)
    result = {"environment": environment(), "limits": limits, "sequential": sequential,
              "releaseId": metadata["releaseId"], "datasetId": metadata["datasetId"],
              "policyVersion": metadata["policyVersion"], "schemaHash": metadata["schemaHash"],
              "queryHash": sha256_file(Path(__file__).with_name("query.py")),
              "concurrent": concurrent, "clients": clients, "memory": peak_memory(),
              "method": "3 warmups per connection; overview plus JSON encoding; no result cache; independent connections per client"}
    write_json(output, result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--constrained", action="store_true")
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--clients", type=int, default=5)
    args = parser.parse_args()
    if args.iterations < 5 or not 1 <= args.clients <= 5:
        parser.error("Use at least 5 iterations and 1 to 5 clients.")
    profile(args.database, args.output, args.constrained, args.iterations, args.clients)
