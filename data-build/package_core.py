"""Build a pinned wheel from the FDA core without writing build files to that checkout."""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from common import content_hash, core_files, sha256_file, source_identity, write_json


def package(source_repo, output_root, snapshot_evidence=None, snapshot_lock=None):
    output_root = Path(output_root).resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    identity = source_identity(source_repo)
    if snapshot_evidence is None:
        expected_lock = json.loads(Path(snapshot_lock).read_text(encoding="utf-8"))
        if identity != expected_lock["source"]:
            raise ValueError("FDA source differs from the pinned source lock.")
    policy_files = {name: digest for name, digest in identity["files"].items() if name.startswith("fda_core/")}
    policy_hash = content_hash(policy_files)
    with tempfile.TemporaryDirectory(prefix="package-", dir=output_root) as directory:
        stage = Path(directory).resolve()
        if stage.parent != output_root:
            raise ValueError("Package staging directory escaped the output root.")
        (stage / "fda_core").mkdir()
        for name in ["pyproject.toml", *policy_files]:
            shutil.copyfile(Path(source_repo) / name, stage / name)
        env = dict(os.environ, SOURCE_DATE_EPOCH="315532800", PIP_CACHE_DIR=str(output_root / "pip-cache"))
        subprocess.run([sys.executable, "-B", "-m", "pip", "wheel", "--no-deps", "--no-build-isolation",
                        "--wheel-dir", str(output_root), str(stage)], env=env, check=True)
    wheel = output_root / "fda_analysis_core-0.1.0-py3-none-any.whl"
    snapshot = (json.loads(Path(snapshot_evidence).read_text(encoding="utf-8"))["metadata"]
                if snapshot_evidence is not None else expected_lock["snapshot"])
    lock = {"formatVersion": 1, "source": identity, "coreVersion": "0.1.0",
            "policyVersion": "fda-core-sha256:" + policy_hash,
            "wheel": {"name": wheel.name, "sha256": sha256_file(wheel)},
            "snapshot": {key: snapshot[key] for key in (
                "manifestSha256", "snapshotSha256", "reportCount", "uniqueReportCount", "pageCount",
                "coverageStart", "coverageEnd", "acquisitionStartedAt", "acquisitionCompletedAt")},
            "build": {"setuptools": importlib.metadata.version("setuptools"),
                      "sourceDateEpoch": 315532800}}
    if core_files(source_repo) != identity["files"]:
        raise ValueError("FDA source changed while packaging.")
    if snapshot_evidence is None and lock != expected_lock:
        raise ValueError("Rebuilt wheel or build metadata differs from the pinned package lock.")
    write_json(output_root / "fda_source.lock.json", lock)
    print(json.dumps({"wheel": str(wheel), "policyVersion": lock["policyVersion"]}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--snapshot-evidence", type=Path)
    parser.add_argument("--snapshot-lock", type=Path, default=Path(__file__).with_name("fda_source.lock.json"))
    args = parser.parse_args()
    package(args.source_repo.resolve(), args.output_root, args.snapshot_evidence, args.snapshot_lock)
