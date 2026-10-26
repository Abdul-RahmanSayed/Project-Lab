# Project Lab

Implementation workspace for the FDA Explorer plan. The agreed MVP in Slices 1-5 is complete and accepted on October 25, 2026, with the documented limits and user-accepted unverified credential-revocation risk in the [closeout review](docs/MVP_ACCEPTANCE_REVIEW.md). Slices 1 and 2 established local feasibility, a packaged canonical policy core, and reproducible read-only database releases. Slice 3 adds a small modular FastAPI backend. Slice 4 adds the React/TypeScript/D3 frontend with shared filters, accessible aggregate views, report browsing and truthful snapshot/request states. Slice 5 publishes the approved checked archive, one Render Free API and the [Pages frontend](https://abdul-rahmansayed.github.io/Project-Lab/#/fda), with verified portfolio integration. Bounded hosted HTTPS parity/performance, actual memory observations, desktop/mobile browser flows, controlled outage recovery, confirmed natural sleep/wake and same-data backend/frontend recovery rehearsals pass with documented limits. Security/licensing limitations remain documented, not universally cleared. Hosting must remain $0. Slice 6 expansion is outside the completed MVP and has not been implemented.

The Explorer follows the portfolio's default dark visual style and typography. The separately approved portfolio Live Demo link and one-sentence description extension were checked on `fda-explorer-link` and merged by Abdul into `master`. Public desktop/mobile homepage checks attempted no FDA requests, and the actual demo-link flow returned the expected filtered result. The remaining uncertainty about the old ingestion key is an explicitly accepted risk, not a verified revocation or a blocker to this scoped MVP closeout.

## Documentation

- [Teaching walkthrough](docs/FDA_EXPLORER_CODE_WALKTHROUGH.md): high-level features, plain-language terminology, detailed execution/data flow, source references and evidence boundaries.
- [MVP acceptance review and October 25 closeout](docs/MVP_ACCEPTANCE_REVIEW.md): agreed Slices 1-5 complete, evidence boundaries retained, and unverified old-key revocation explicitly accepted as a remaining risk.
- [Baseline plan](docs/FDA_DASHBOARD_PLAN.md): unchanged copy of the supplied October 8 plan.
- [Slice 1 assumptions and behavior contract](docs/SLICE_1_ASSUMPTIONS.md).
- [Slice 1 measured results](docs/SLICE_1_RESULTS.md).
- [Slice 2 measured results and remaining performance gate](docs/SLICE_2_RESULTS.md).
- [Later decisions and current performance expectations](docs/FDA_EXPLORER_DECISIONS.md): the user-approved default-overview threshold supersedes the plan's provisional two-second target.
- [Prepared-default performance follow-up](docs/PERFORMANCE_FOLLOWUP_RESULTS.md): the local default path passes; standby-affected runs and filtered costs are retained and qualified.
- [October 15 results review](docs/RESULTS_REVIEW_2026-10-15.md): historical review and then-blocked release access; access was restored during Slice 3.
- [Approved smaller backend scope](docs/SLICE_3_SCOPE.md): October 20 decisions and deliberate simplifications.
- [Implemented API contract](docs/API_CONTRACT_IMPLEMENTED.md): requests, response models, paging, limits and failure behavior.
- [Slice 3 results](docs/SLICE_3_RESULTS.md): correctness, actual HTTP timings, resource use, release access and remaining limitations.
- [Approved Slice 4 scope](docs/SLICE_4_SCOPE.md) and [local frontend results](docs/SLICE_4_RESULTS.md).
- [Slice 5A hosting review and deployment proposal](docs/SLICE_5_DEPLOYMENT_PROPOSAL.md): published limits, account checks and proposed setup; local preparation was subsequently approved, while external actions/hosted acceptance remain pending.
- [Slice 5B local preparation results](docs/SLICE_5_LOCAL_PREPARATION_RESULTS.md) and [deployment guide](deployment/README.md): archive/container/origin wiring and local HTTPS evidence, with Linux/hosted limits explicit.
- [October 21 Linux follow-up](docs/SLICE_5_LINUX_RESULTS.md): checked container build, representative Python-reference parity, five-client HTTP measurements and memory within 0.1 CPU/512 MB; hosted/security checks remain pending.
- [Local runtime refresh](docs/SLICE_5_RUNTIME_REFRESH_RESULTS.md): Python/base and hash-pinned build-tool maintenance, packaging-tool removal, Linux API regressions and repeated constrained HTTP/resource checks; no deployment or full-image security clearance.
- [Historical hosted acceptance record](docs/SLICE_5_HOSTED_RESULTS.md): approved public archive, Free API and Pages frontend, initial HTTPS/browser/recovery evidence; later follow-ups and the closeout review resolve the milestone's functional gates.
- [Opt-in memory log follow-up](docs/SLICE_5_MEMORY_LOG_RESULTS.md): local checks plus actual Render memory and HTTPS parity/performance evidence, with diagnostic cleanup linked to the later recovery record.
- [Hosted recovery follow-up](docs/SLICE_5_RECOVERY_RESULTS.md): logging disabled, actual provider outage/fallback and recovery, mobile screenshots and confirmed natural sleep/wake; subsequent portfolio verification is recorded separately.
- [Portfolio integration results](docs/SLICE_5_PORTFOLIO_RESULTS.md): approved two-line edit, passing local typecheck/build, subsequent public desktop/mobile no-FDA-request checks and actual demo-link flow; the final scope/risk decision is linked to the closeout review.
- [Frontend guide](web/README.md): run/build/test commands, release-bound saved data, selection state and request handling.
- [Historical FastAPI draft](docs/FASTAPI_CONTRACT.md): superseded where the approved smaller scope differs, including unsigned bookmarks and no application waiting queue.
- [Completion follow-ups](docs/COMPLETION_FOLLOWUPS.md): after all slices are complete and working, remind Abdul about the teaching walkthrough, resume update, and Flex fintech application.

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

Preparation stages and validates a whole bundle, then publishes it under a content-derived release directory. A byte-identical existing release can be reused; differing content cannot replace it. Use a separate output root for an independent rebuild. The release contains the database, metadata, page inventory, labeled saved overview, and artifact checksums. Timings stay outside the deterministic release. All databases, wheels, generated evidence, and the environment are excluded by `.gitignore`. The user has since initialized Project Lab on `development`; this performance follow-up does not commit or push changes.

The source lock deliberately identifies local working-tree content, not just the base commit. Source/core/schema/query changes require a reviewed new pin and full rebuild; changing the source lock is not an automatic refresh. Rebuilding the pinned wheel does not depend on Slice 1's generated evidence. Its SHA-256 must match the wheel pin. The original plan and Slice 1 reports remain historical; their old database commands do not apply to schema version 2.

## Demonstrate a Real Filtered Query

After the preparation commands above:

```powershell
.\.venv\Scripts\python.exe -B data-build\query.py --database "$releaseDir\fda.sqlite3" --start-year 2024 --end-year 2026 --product CARROTS
Get-Content -Raw "$releaseDir\saved-overview.json" | ConvertFrom-Json
```

The filtered query returns 149 reports, 123 valid ages, and 26 missing/invalid ages, with 122 reports in 2024 and 27 in 2025. SQLite is read-only; no pandas, NumPy, Matplotlib, or FDA policy imports occur at query time. Verification saves the same response as `filtered-example.json` in its output directory. The saved default overview explicitly says `Saved overview / data snapshot`, has `isLive: false`, and includes acquisition time and release identity. It is not a UI or a live FDA refresh.

## Profile Under Constraints

The historical SQL-only benchmark applies a Windows Job Object hard CPU cap of approximately 0.1 core and a 512 MiB committed-memory cap to its own process only. It measures sequential queries, then five independent SQLite connections, without a result cache:

```powershell
.\.venv\Scripts\python.exe -B data-build\profile.py --database "$releaseDir\fda.sqlite3" --output generated\rerun\profile-constrained.json --constrained --iterations 5 --clients 5
```

The original two-second target is historical, not a current requirement. The user now requires **warm request latency p95 strictly below ten seconds for the default all-year overview with five simultaneous requesters**, within the actual free compute/memory/storage limits. The historical SQL-only default p95 was 13.05 seconds. Maximum latency remains a diagnostic metric, not the acceptance threshold. See the [decision record](docs/FDA_EXPLORER_DECISIONS.md). Preparation belongs offline, not in the constrained service process.

## Prepared Default Reuse

`data-build/runtime.py` validates the existing release once, verifies the query-code pin, and keeps one immutable, labeled default response. Only the exact all-year/no-product selection uses those prepared bytes. Changed filters still use the existing read-only SQL path and keep the raw search, counting, normalization, and age policies. Every response explicitly describes a saved data snapshot, not live FDA data. This runtime adapter has no filtered-response cache; the later HTTP backend adds the five-job work limit described below.

The historical controlled short run measured default p95 **2.08 ms**, mixed uncached SQL p95 **8.91 seconds**, and constrained process peak **76.63 MiB**, before HTTP handling existed. Two longer runs overlapped Modern Standby and are retained as qualified evidence. Do not compare these directly with the [Slice 3 HTTP results](docs/SLICE_3_RESULTS.md) as a controlled speedup experiment.

After creating `$releaseDir` above, run the new tests and independent verification, then profile:

```powershell
.\.venv\Scripts\python.exe -B tests\test_overview_runtime.py --source-repo $fdaSource -v
.\.venv\Scripts\python.exe -B tests\test_windows_limits.py -v
.\.venv\Scripts\python.exe -B data-build\verify_runtime.py --source-repo $fdaSource --release-directory $releaseDir --output-dir generated\rerun\runtime-verification
.\.venv\Scripts\python.exe -B data-build\profile_runtime.py --release-directory $releaseDir --output generated\rerun\runtime-profile-constrained.json --rounds 20 --clients 5 --constrained --keep-awake
```

This profiler measures repeated defaults, repeated uncached carrots, mixed uncached SQL selections, and defaults interleaved with filtered work. Timing starts before task submission and includes dispatch/synchronization/scheduling wait. SQL connections are opened and closed per request; prepared defaults open none. Twenty rounds produce 100 measured requests per scenario in five-request waves, not an unbounded arrival queue. `--keep-awake` temporarily requests both system and display activity (needed for this machine's Modern Standby) and restores the previous thread state on exit; it does not change saved power settings or prevent deliberate user sleep. Use `--rounds 5` for a shorter 25-request diagnostic per scenario. This is the pre-HTTP runtime experiment; use the backend benchmark below to include actual local web requests.

## Run the Local Backend

Use a separate lightweight API environment. This installs the existing serving modules with the backend, so it runs without importing through a machine-specific source path. It does not install pandas, NumPy, Matplotlib or the FDA analysis core into the API environment.

```powershell
python -m venv .venv-api
.\.venv-api\Scripts\python.exe -m pip install setuptools==84.2.1 -r backend\requirements.lock.txt
.\.venv-api\Scripts\python.exe -m pip install --no-deps --no-build-isolation .
$buildRecord = Get-Content -Raw generated\backend\release\preparation.json | ConvertFrom-Json
$releaseDir = $buildRecord.releaseDirectory
$releaseId = $buildRecord.release.releaseId
.\.venv-api\Scripts\python.exe -B -m backend.preflight --release-directory $releaseDir --release-id $releaseId --output generated\backend\preflight.json
.\.venv-api\Scripts\python.exe -B -m backend.run --release-directory $releaseDir --release-id $releaseId --port 8765
```

If preparing into a different output root, read that root's `preparation.json` instead. The current rebuilt copy is under `generated/backend/release`; the original `generated/slice2/final-release-a` copy is also readable after Abdul's targeted Windows permission repair. Both have the same checked release identity and database bytes. New Windows preparation directories may still require an explicit permission/inheritance check; the pinned builder was not silently repinned to alter publication permissions.

Open [interactive API docs](http://127.0.0.1:8765/docs), [readiness](http://127.0.0.1:8765/readyz), or [the 2024-2026 CARROTS overview](http://127.0.0.1:8765/api/v1/fda/explore?startYear=2024&endYear=2026&productFilter=CARROTS). This is a local JSON API, not the dashboard frontend. Stop a terminal-run server with Ctrl+C. The runner binds only to `127.0.0.1` and starts one worker.

The default response reuses one checked prepared payload. Changed selections query SQLite; there is no general result cache. Up to five SQL jobs run at once, with **no application waiting queue**; excess SQL requests receive `503 SERVICE_BUSY` and `Retry-After: 2`. The 30-second SQL-backed budget includes dispatch, query, validation and encoding. Disconnects/timeouts signal cancellation, and a worker keeps its slot until it actually exits. The server also has a finite built-in connection/task limit; that is not a traffic-flood defense.

## Verify the Backend

Run after the data preparation and API installation above. Tests require the separate test dependency pins. The independent HTTP oracle uses the analysis environment and the original Python analysis, not the API's SQL answers.

```powershell
.\.venv-api\Scripts\python.exe -m pip install -r backend\requirements-test.lock.txt
.\.venv-api\Scripts\python.exe -B -m backend.test_api --release-directory $releaseDir --release-id $releaseId --output generated\backend\api-tests.json
.\.venv\Scripts\python.exe -B data-build\api_oracle.py --source-repo $fdaSource --output generated\backend\api-oracle.json
.\.venv-api\Scripts\python.exe -B -m backend.benchmark --release-directory $releaseDir --release-id $releaseId --oracle generated\backend\api-oracle.json --output-directory generated\backend\http-acceptance --rounds 1 --port 8876
.\.venv-api\Scripts\python.exe -B -m backend.benchmark --release-directory $releaseDir --release-id $releaseId --output-directory generated\backend\http-constrained-final --rounds 10 --constrained --port 8876
```

The benchmark starts and stops its own local server. The constrained run applies approximately 0.1 CPU core and a 512 MiB committed-memory cap to that server only, and temporarily prevents idle sleep. Ten five-client waves produce 50 observations per main scenario. Timing includes dispatch, HTTP handling, query work, validation, encoding and receiving the full body. Busy responses are counted separately, never disguised as fast successful queries. This still excludes browser rendering, internet transfer, service wake-up and actual hosted scheduling. See the [results](docs/SLICE_3_RESULTS.md) before drawing hosting conclusions.

## Run the Local Frontend

Start the checked backend at `127.0.0.1:8765` using the commands above, then run from this workspace with Node 24.13+ (24.x):

```powershell
npm.cmd --prefix web ci
npm.cmd --prefix web run build
npm.cmd --prefix web run preview
```

Open [FDA Explorer](http://127.0.0.1:4173/). The local preview proxies `/api` requests to the existing backend; no CORS or backend source change is required. For editing with hot reload, use `npm.cmd --prefix web run dev` at `http://127.0.0.1:5173/` instead. If a port is occupied, pass another with `-- --port 4174` or `-- --port 5174`; keep the verified API target separate. The [frontend guide](web/README.md) covers configuration and tests.

The frontend bundles only the checked public metadata, default aggregate response and generated API contract, not the database or raw report pages. That saved default remains labeled, including when the API is unavailable. Custom selections are queried only when the API is ready. Old data keeps its original displayed-selection label while a newer query is pending or fails. Hash URLs preserve the exact committed search, years, release, tab and page size. No general cache, browser persistence, extra queue or plugin framework was added.

After a separately reviewed release change, regenerate the frontend artifacts from that selected checked release before rebuilding:

```powershell
.\.venv-api\Scripts\python.exe -B data-build\frontend_bundle.py --release-directory $releaseDir --release-id $releaseId
npm.cmd --prefix web run build
```

The build checks bundle hashes and default/release identity, generates TypeScript from OpenAPI, then typechecks and builds. It never downloads FDA data, prepares a database or selects a newer release automatically. Local preview wiring is not a deployed API-origin/CORS configuration or hosted wake-up test.

## Local Files

`data-build/package_core.py` builds the FDA-owned standard-library-only core wheel without writing build artifacts to the FDA checkout. `prepare.py` streams canonically validated pages through the installed core, checks the snapshot pin, and publishes an atomic release. `schema.py` owns versioned tables and annual aggregates. `query.py` reuses each selected set within one overview statement and uses prepared annual totals for year-only selections. `verify.py` compares both the extracted CLI and the independently recovered original CLI against SQL, and rehashes every source page. `verify_runtime.py` additionally checks prepared/SQL dispatch against that independent oracle; `profile_runtime.py` measures the pre-HTTP request path. `backend/app.py` owns startup and shared errors, `backend/jobs.py` owns SQL work limits/cancellation, and `backend/fda/` owns FDA routes, schemas, lifecycle and report projections. `backend/preflight.py`, `backend/test_api.py` and `backend/benchmark.py` provide offline serving checks, contract regressions and actual HTTP evidence.

Slice 2's authorized FDA changes are limited to `part2.py`, the new `fda_core` package, and `pyproject.toml`. Slices 3 and 4 add no FDA-source or portfolio edits. The downloader, saved raw data, source README and ignored upstream tests/review notes remain unchanged. Slice 4 includes no deployment, accounts, repository publication, commit or push; Abdul made the preceding local checkpoint commit. The upstream stale-test/publication question, reproducible CI/container packaging and current free-provider eligibility remain unresolved; they are not silently treated as accepted work.
