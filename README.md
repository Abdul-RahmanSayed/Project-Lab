# Project Lab

Local implementation workspace for the FDA Explorer plan. Slices 1 and 2 are complete: local feasibility, a packaged canonical policy core, and reproducible read-only database releases. Intended later architecture: React/TypeScript/D3, a modular FastAPI backend, and a prepared SQLite snapshot with $0 hosting and a labeled saved overview during service wake-up. The API and frontend have not started.

## Documentation

- [Baseline plan](docs/FDA_DASHBOARD_PLAN.md): unchanged copy of the supplied October 8 plan.
- [Slice 1 assumptions and behavior contract](docs/SLICE_1_ASSUMPTIONS.md).
- [Slice 1 measured results](docs/SLICE_1_RESULTS.md).
- [Slice 2 measured results and remaining performance gate](docs/SLICE_2_RESULTS.md).
- [Later decisions and current performance expectations](docs/FDA_EXPLORER_DECISIONS.md): the user-approved default-overview threshold supersedes the plan's provisional two-second target.

## Reproduce Locally

Python 3.14.2 and SQLite 3.50.4 were used for these measurements. Run from this folder in PowerShell. Initial dependency installation requires network access; packaging, preparation, queries, and verification use local files only. The pinned FDA checkout, including the uncommitted Slice 2 core extraction, must match `data-build/fda_source.lock.json`. Verification also requires the original revision in its local Git history.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r data-build\requirements.lock.txt
$fdaSource = 'C:\Users\abdul\OneDrive\Documents\GitHub\FDA-Food-Safety-Data-Pipeline'
.\.venv\Scripts\python.exe -B data-build\package_core.py --source-repo $fdaSource --output-root generated\rerun\package
.\.venv\Scripts\python.exe -m pip install --no-index --no-deps --force-reinstall generated\rerun\package\fda_analysis_core-0.1.0-py3-none-any.whl
.\.venv\Scripts\python.exe -B tests\test_fda_spike.py --source-repo $fdaSource -v
.\.venv\Scripts\python.exe -B tests\test_slice2.py --source-repo $fdaSource -v
.\.venv\Scripts\python.exe -B data-build\prepare.py --source-repo $fdaSource --output-root generated\rerun\release
$buildRecord = Get-Content -Raw generated\rerun\release\preparation.json | ConvertFrom-Json
$releaseDir = $buildRecord.releaseDirectory
.\.venv\Scripts\python.exe -B data-build\verify.py --source-repo $fdaSource --database "$releaseDir\fda.sqlite3" --output-dir generated\rerun\verification --iterations 30
```

Preparation stages and validates a whole bundle, then publishes it under a content-derived release directory. A byte-identical existing release can be reused; differing content cannot replace it. Use a separate output root for an independent rebuild. The release contains the database, metadata, page inventory, labeled saved overview, and artifact checksums. Timings stay outside the deterministic release. All databases, wheels, generated evidence, and the environment are excluded by `.gitignore`; no Git repository has been initialized here.

The source lock deliberately identifies local working-tree content, not just the base commit. Source/core/schema/query changes require a reviewed new pin and full rebuild; changing the source lock is not an automatic refresh. Rebuilding the pinned wheel does not depend on Slice 1's generated evidence. Its SHA-256 must match the wheel pin. The original plan and Slice 1 reports remain historical; their old database commands do not apply to schema version 2.

## Demonstrate a Real Filtered Query

After the preparation commands above:

```powershell
.\.venv\Scripts\python.exe -B data-build\query.py --database "$releaseDir\fda.sqlite3" --start-year 2024 --end-year 2026 --product CARROTS
Get-Content -Raw "$releaseDir\saved-overview.json" | ConvertFrom-Json
```

The filtered query returns 149 reports, 123 valid ages, and 26 missing/invalid ages, with 122 reports in 2024 and 27 in 2025. SQLite is read-only; no pandas, NumPy, Matplotlib, or FDA policy imports occur at query time. Verification saves the same response as `filtered-example.json` in its output directory. The saved default overview explicitly says `Saved overview / data snapshot`, has `isLive: false`, and includes acquisition time and release identity. It is not a UI or a live FDA refresh.

## Profile Under Constraints

On Windows, this applies a Job Object hard CPU cap of approximately 0.1 core and a 512 MiB committed-memory cap to its own process only. It measures sequential queries, then five independent SQLite connections, without a result cache:

```powershell
.\.venv\Scripts\python.exe -B data-build\profile.py --database "$releaseDir\fda.sqlite3" --output generated\rerun\profile-constrained.json --constrained --iterations 5 --clients 5
```

The original two-second target is historical, not a current requirement. The user now requires **warm request latency p95 strictly below ten seconds for the default all-year overview with five simultaneous requesters**, within the actual free compute/memory/storage limits. The existing default-overview p95 of 13.05 seconds does not meet that goal. Maximum latency remains a diagnostic metric, not the acceptance threshold. See the [decision record](docs/FDA_EXPLORER_DECISIONS.md). Preparation belongs offline, not in the constrained service process. No further implementation slice is authorized by this documentation update.

## Local Files

`data-build/package_core.py` builds the FDA-owned standard-library-only core wheel without writing build artifacts to the FDA checkout. `prepare.py` streams canonically validated pages through the installed core, checks the snapshot pin, and publishes an atomic release. `schema.py` owns versioned tables and annual aggregates. `query.py` reuses each selected set within one overview statement and uses prepared annual totals for year-only selections. `verify.py` compares both the extracted CLI and the independently recovered original CLI against SQL, and rehashes every source page. The two local test suites cover policy/CLI compatibility, failure handling, release integrity, and read-only queries.

Slice 2's authorized FDA changes are limited to `part2.py`, the new `fda_core` package, and `pyproject.toml`. The downloader, saved raw data, source README, ignored upstream tests/review notes, and portfolio remain unchanged. No frontend, FastAPI service, deployment, accounts, repository publication, commit, or push is included.
