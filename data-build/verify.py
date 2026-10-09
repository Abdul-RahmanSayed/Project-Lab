"""Compare SQLite with the current Python oracle and measure isolated warm queries."""

import argparse
import gc
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys
import time

from common import environment, load_policy, peak_memory, sha256_file, source_identity, write_json
from legacy import ensure_legacy
from query import explore, open_database, overview_sql, rankings, selected_ids, selection


CASES = [
    ("overall", 2002, 2026, None),
    ("year_2024", 2024, 2024, None),
    ("product_carrots", 2002, 2026, "cArRoTs"),
    ("year_product_carrots", 2024, 2026, "CARROTS"),
    ("product_vitamin_d3", 2002, 2026, "VITAMIN D3"),
    ("empty_selection", 2002, 2026, "slice1-no-such-product-9c812b"),
    ("literal_percent", 2002, 2026, "%"),
    ("literal_underscore", 2002, 2026, "_"),
    ("partial_2026", 2026, 2026, None),
]
ABS_TOLERANCE = 1e-10
REL_TOLERANCE = 1e-12


def cases():
    return [(name, {"startYear": start, "endYear": end, "productFilter": product})
            for name, start, end, product in CASES]


def oracle_result(policy, reports, filters):
    import numpy as np
    frame = policy.makeDataFrame(policy.selectReports(reports, filters))
    ages = policy.getValidAges(frame)
    counts, _ = np.histogram(ages, bins=np.arange(0, policy.maxAge + 2))
    genders = frame["gender"].fillna("Unknown").value_counts()
    columns = (("products", "suspectProducts"), ("outcomes", "outcomes"), ("reactions", "reactions"))
    overview = {
        "appliedFilters": filters, "selectedCount": len(frame), "validAgeCount": len(ages),
        "missingAgeCount": len(frame) - len(ages), "ageMeans": policy.getAgeAverages(frame),
        "yearCounts": [[int(year), int(count)] for year, count in policy.getYearCounts(frame, filters).items()],
        "ageHistogram": [[age, int(count)] for age, count in enumerate(counts)],
        "genderCounts": [[gender, int(genders.get(gender, 0))] for gender in ("Female", "Male", "Unknown")],
        "rankings": {key: [list(item) for item in policy.getTopTerms(frame, column)] for key, column in columns}}
    return {"overview": overview,
            "selectedIds": sorted(report["report_number"] for report in frame["report"]),
            "allRankings": {key: [list(item) for item in policy.getTopTerms(frame, column, limit=sys.maxsize)]
                            for key, column in columns}}


def assert_equal(actual, expected, path="result"):
    if isinstance(expected, float):
        if actual is None or not math.isclose(actual, expected, rel_tol=REL_TOLERANCE, abs_tol=ABS_TOLERANCE):
            raise AssertionError(f"{path}: {actual!r} != {expected!r}")
    elif isinstance(expected, dict):
        for key, value in expected.items():
            assert_equal(actual[key], value, path + "." + key)
    elif isinstance(expected, list):
        if len(actual) != len(expected):
            raise AssertionError(f"{path}: lengths differ ({len(actual)} != {len(expected)})")
        for index, (left, right) in enumerate(zip(actual, expected)):
            assert_equal(left, right, f"{path}[{index}]")
    elif actual != expected:
        raise AssertionError(f"{path}: {actual!r} != {expected!r}")


def build_oracles(source_repo, output, baseline=False):
    started = time.perf_counter()
    policy = load_policy(ensure_legacy(source_repo) if baseline else source_repo)
    reports = policy.loadReports(Path(source_repo) / "data")
    results = {}
    for name, filters in cases():
        case_started = time.perf_counter()
        results[name] = oracle_result(policy, reports, filters)
        print(f"Oracle {name}: {results[name]['overview']['selectedCount']:,} reports; "
              f"{time.perf_counter() - case_started:.3f}s", flush=True)
        gc.collect()
    write_json(output, {"results": results, "oracleSeconds": time.perf_counter() - started,
                        "memory": peak_memory(), "environment": environment()})


def nearest_rank(values, fraction):
    return sorted(values)[math.ceil(len(values) * fraction) - 1]


def measure_queries(database, oracle_path, output, iterations):
    oracle = json.loads(Path(oracle_path).read_text(encoding="utf-8"))
    benchmark = {}
    connection = open_database(database)
    try:
        for name, filters in cases():
            expected = oracle["results"][name]
            actual = explore(connection, filters)
            assert_equal(actual, expected["overview"], name)
            assert_equal(selected_ids(connection, filters), expected["selectedIds"], name + ".selectedIds")
            assert_equal(rankings(connection, filters, sys.maxsize), expected["allRankings"], name + ".allRankings")
        del oracle
        gc.collect()
        # Parity allocations are excluded from the separate runtime-only benchmark process.
        for name, filters in cases():
            durations = []
            for _ in range(3):
                explore(connection, filters)
            for _ in range(iterations):
                started = time.perf_counter_ns()
                result = explore(connection, filters)
                payload = json.dumps(result, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode()
                durations.append((time.perf_counter_ns() - started) / 1e6)
            cte, params = selection(connection, filters)
            params["limit"] = 25
            plan = [row[3] for row in connection.execute(
                "EXPLAIN QUERY PLAN " + overview_sql(cte, filters), params)]
            benchmark[name] = {
                "filters": filters, "parity": "pass", "selectedCount": result["selectedCount"],
                "validAgeCount": result["validAgeCount"], "ageMeans": result["ageMeans"],
                "warmLatencyMs": {"samples": iterations, "min": min(durations),
                                  "median": statistics.median(durations), "p95": nearest_rank(durations, .95),
                                  "max": max(durations)}, "overviewJsonBytes": len(payload), "selectionPlan": plan}
            print(f"SQLite {name}: parity pass; warm p95 {benchmark[name]['warmLatencyMs']['p95']:.2f}ms", flush=True)
            if name == "year_product_carrots":
                write_json(Path(output).parent / "filtered-example.json", result)
        write_json(output, {"cases": benchmark, "memoryIncludingParity": peak_memory(),
                            "environment": environment(),
                            "method": "One SQL overview statement; sequential read-only connection; 3 warmups; no result cache; overview + JSON encoding.",
                            "meanTolerance": {"absolute": ABS_TOLERANCE, "relative": REL_TOLERANCE}})
    finally:
        connection.close()


def runtime_memory(database, output):
    connection = open_database(database)
    for _, filters in cases():
        for _ in range(3):
            json.dumps(explore(connection, filters), allow_nan=False)
    connection.close()
    heavy = [name for name in ("pandas", "numpy", "matplotlib") if name in sys.modules]
    if heavy:
        raise AssertionError(f"Runtime unexpectedly imported analysis dependencies: {heavy}")
    write_json(output, {"memory": peak_memory(), "environment": environment(), "analysisLibrariesLoaded": heavy})


def run(source_repo, database, output_dir, iterations):
    source_before = source_identity(source_repo)
    output_dir.mkdir(parents=True, exist_ok=True)
    script = str(Path(__file__).resolve())
    commands = [
        ["--stage", "oracle", "--source-repo", str(source_repo), "--output-dir", str(output_dir)],
        ["--stage", "baseline", "--source-repo", str(source_repo), "--output-dir", str(output_dir)],
        ["--stage", "queries", "--database", str(database), "--output-dir", str(output_dir),
         "--iterations", str(iterations)],
        ["--stage", "runtime", "--database", str(database), "--output-dir", str(output_dir)],
    ]
    for arguments in commands:
        subprocess.run([sys.executable, "-B", script, *arguments], check=True)
    preparation = json.loads((database.parent.parent / "preparation.json").read_text(encoding="utf-8"))
    for page in preparation["pageInventory"]:
        if sha256_file(source_repo / "data" / page["path"]) != page["sha256"]:
            raise AssertionError(f"Source page changed: {page['path']}")
    if sha256_file(source_repo / "data" / "manifest.json") != preparation["metadata"]["manifestSha256"]:
        raise AssertionError("Source manifest changed.")
    if source_identity(source_repo) != source_before or source_before != preparation["metadata"]["source"]:
        raise AssertionError("Source policy identity changed.")
    if sha256_file(database) != preparation["databaseSha256"]:
        raise AssertionError("Read-only queries changed the database.")
    oracle = json.loads((output_dir / "oracle.json").read_text(encoding="utf-8"))
    queries = json.loads((output_dir / "queries.json").read_text(encoding="utf-8"))
    runtime = json.loads((output_dir / "runtime.json").read_text(encoding="utf-8"))
    baseline = json.loads((output_dir / "oracle-baseline.json").read_text(encoding="utf-8"))
    assert_equal(oracle["results"], baseline["results"], "pre-extraction CLI")
    historical_path = Path(__file__).resolve().parents[1] / "generated" / "slice1" / "oracle.json"
    if historical_path.exists():
        historical = json.loads(historical_path.read_text(encoding="utf-8"))
        assert_equal(oracle["results"], historical["results"], "Slice 1 oracle")
    report = {"preparation": {key: value for key, value in preparation.items() if key != "pageInventory"},
              "oracle": {key: value for key, value in oracle.items() if key != "results"},
              "queries": queries, "runtime": runtime,
              "audit": {"sourcePoliciesAndSnapshotUnchanged": True, "databaseUnchangedByQueries": True,
                        "matchesPreExtractionCli": True, "baselineRevision": source_before["revision"],
                        "snapshotPagesRehashed": len(preparation["pageInventory"])}}
    write_json(output_dir / "results.json", report)
    print("All parity cases passed, including the pre-extraction oracle; source and database hashes are unchanged.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("all", "oracle", "baseline", "queries", "runtime"), default="all")
    parser.add_argument("--source-repo", type=Path)
    parser.add_argument("--database", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--iterations", type=int, default=30)
    args = parser.parse_args()
    if args.iterations < 5:
        parser.error("Use at least five measured iterations.")
    if args.stage in ("all", "oracle", "baseline") and args.source_repo is None:
        parser.error("--source-repo is required for oracle/all stages.")
    if args.stage not in ("oracle", "baseline") and args.database is None:
        parser.error("--database is required for query/runtime/all stages.")
    if args.stage == "oracle":
        build_oracles(args.source_repo, args.output_dir / "oracle.json")
    elif args.stage == "baseline":
        build_oracles(args.source_repo, args.output_dir / "oracle-baseline.json", baseline=True)
    elif args.stage == "queries":
        measure_queries(args.database, args.output_dir / "oracle.json", args.output_dir / "queries.json", args.iterations)
    elif args.stage == "runtime":
        runtime_memory(args.database, args.output_dir / "runtime.json")
    else:
        run(args.source_repo.resolve(), args.database.resolve(), args.output_dir.resolve(), args.iterations)
