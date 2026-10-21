"""Recheck full Python/SQL parity, then verify prepared-default dispatch independently."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from common import environment, peak_memory, sha256_file, source_identity, write_json
from prepare import validate_release
from runtime import OverviewRuntime
from verify import assert_equal, cases


def runtime_memory(release_directory, output):
    started = time.perf_counter()
    reader = OverviewRuntime(release_directory)
    startup = time.perf_counter() - started
    for _, filters in cases():
        for _ in range(3):
            reader.read(filters)
    heavy = [name for name in ("pandas", "numpy", "matplotlib", "fda_core") if name in sys.modules]
    if heavy:
        raise AssertionError("Runtime loaded analysis/policy packages: " + repr(heavy))
    write_json(output, {"startupSeconds": startup, "memory": peak_memory(), "runtime": reader.describe(),
                        "analysisOrPolicyPackagesLoaded": heavy, "environment": environment()})


def verify(source_repo, release_directory, output):
    output.mkdir(parents=True, exist_ok=True)
    source_before = source_identity(source_repo)
    release_before = validate_release(release_directory)
    subprocess.run([sys.executable, "-B", str(Path(__file__).with_name("verify.py")),
                    "--source-repo", str(source_repo), "--database", str(release_directory / "fda.sqlite3"),
                    "--output-dir", str(output / "sql-parity"), "--iterations", "30"], check=True)
    baseline = json.loads((output / "sql-parity" / "oracle-baseline.json").read_text(encoding="utf-8"))
    reader = OverviewRuntime(release_directory)
    results = {}
    for name, filters in cases():
        payload = reader.read(filters)
        response = json.loads(payload)
        assert_equal(response["overview"], baseline["results"][name]["overview"], name)
        source = "prepared-default" if filters == reader.default_filters else "sqlite"
        if response["source"] != source or response["isLive"] is not False or response["releaseId"] != reader.release_id:
            raise AssertionError("Incorrect response provenance: " + name)
        results[name] = {"parity": "pass", "source": source, "selectedCount": response["overview"]["selectedCount"],
                         "payloadBytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}
        print(f"Runtime {name}: {source}; parity pass", flush=True)
    subprocess.run([sys.executable, "-B", str(Path(__file__).resolve()), "--stage", "memory",
                    "--release-directory", str(release_directory), "--output-dir", str(output)], check=True)
    if source_identity(source_repo) != source_before or validate_release(release_directory) != release_before:
        raise AssertionError("Source or release changed during runtime verification.")
    write_json(output / "results.json", {"runtime": reader.describe(), "cases": results,
        "runtimeCodeSha256": sha256_file(Path(__file__).with_name("runtime.py")),
        "isolated": json.loads((output / "runtime-memory.json").read_text(encoding="utf-8")),
        "sqlParityEvidence": str(output / "sql-parity" / "results.json"),
        "audit": {"sourceUnchanged": True, "releaseArtifactsUnchanged": True,
                  "independentPreExtractionOracleMatched": True, "savedSelectionUsesPreparedBytes": True}})
    print("Runtime and complete SQL/original-Python parity passed; release and source are unchanged.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("all", "memory"), default="all")
    parser.add_argument("--source-repo", type=Path)
    parser.add_argument("--release-directory", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.stage == "all" and args.source_repo is None:
        parser.error("--source-repo is required for full verification.")
    if args.stage == "memory":
        runtime_memory(args.release_directory.resolve(), args.output_dir.resolve() / "runtime-memory.json")
    else:
        verify(args.source_repo.resolve(), args.release_directory.resolve(), args.output_dir.resolve())
