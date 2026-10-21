# Slice 3: Smaller Local Backend Results

Completed locally on October 20, 2026, within the [approved scope](SLICE_3_SCOPE.md). **The local backend slice passes. The complete dashboard is not finished.** Frontend, deployment, accounts, repository publication, commits and pushes remain outside this slice.

## Plain-Language Summary

The saved FDA data can now answer real local web requests. A caller can ask for the overview, choose years and a raw product-name search, page through matching reports, and inspect retained report details. The API also says which saved snapshot it is using and whether that snapshot is ready.

The unchanged default overview is reused instead of calculated five times. Other selections are genuinely queried, not answered with unrelated saved numbers. Five database jobs may run together; extra database work gets an explicit busy response instead of building an invisible waiting line. Cancelled work retains its slot until it really stops.

## Release Access and Identity

The original saved release was unreadable both inside and outside the sandbox. A targeted inheritance change from the ordinary process failed; bypassing the sandbox did not confer Windows administrator privileges. Preparation reproduced a private directory with inheritance disabled, consistent with restricted temporary-directory permissions surviving publication. The old directory's own owner/access list could not be inspected before repair, so its exact ownership was not proven.

While access was blocked, the unchanged pinned builder reproduced the same release at `generated/backend/release/18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194`. Inheritance was enabled on that exact new directory. Abdul subsequently repaired the original directory's ownership/inheritance in an administrator PowerShell window. The API's full startup checks now accept the original copy too; both copies have identical database bytes and release identity. Other historical experimental directories were not repaired or needed for acceptance.

- Release: `fda-release-sha256:18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194`.
- Database SHA-256: `bdfd771ede151a2784a83ff1e9ba1faad727491cce2bddf73a0499521b4d475f`.
- Database: **62,152,704 bytes / 59.27 MiB**; **97,652 reports**, **987 source pages**.
- Same pinned snapshot and policy; no source-lock, preparer, schema, query or canonical-policy changes.
- Rebuild: **24.39 seconds**, **52.01 MiB** preparation-process peak resident memory. These are the recorded rebuild measurements from this slice, not another preparation run after permission repair.
- January 1, 2026 remains actual 2026 data: **24 reports**, explicitly a partial year, although downloaded in the final 2025 window.

The original Windows publication-permissions issue was worked around, not automatically fixed in the pinned builder. A future builder change requires its own reviewed pin/rebuild. No broad OneDrive permissions were changed by this slice.

## What Is Implemented

The [implemented contract](API_CONTRACT_IMPLEMENTED.md) describes the routes and executable schemas. Shared startup/errors/job ownership live in `backend/`; FDA schemas, selection parsing, lifecycle and report queries live in `backend/fda/`. Existing serving modules are packaged unchanged rather than copied or imported through an absolute FDA-source path.

Included: health/readiness, snapshot metadata, overview, deterministic report pages and retained-field detail; strict parameters and size limits; release/filter-bound prepared response; safe errors; bounded SQL work and cooperative cancellation. Report IDs use ordinary query fields. Unsigned next-page bookmarks avoid a signing secret and cannot change the current selection. There is no general filtered-response cache or application pending queue.

Startup validates the selected release and prepared public response. Bad/missing/unreadable inputs leave health available but FDA readiness/data unavailable. It never downloads or rebuilds on a visitor request. The API uses read-only SQLite connections and does not import pandas, NumPy, Matplotlib or the FDA analysis core while serving.

## Correctness and Tests

**41 local regression tests pass**: eight SQL/semantic, ten core/CLI/release, eight prepared-runtime, three temporary-sleep-guard, and twelve API tests. The existing 29 were rerun once as a final batch, and the final installed API package passed its twelve tests. `pip check` reports no broken requirements.

API coverage includes exact prepared-default selection and conditional responses; changed-year SQL dispatch; literal `%`, `_`, `+`, whitespace/case preservation and Unicode inputs; null/empty results; invalid/duplicate/unknown parameters; page sizes/order/bookmark context; report details restricted to the current selection; restart bookmarks; wrong-release/missing/corrupt/malformed/unreadable startup; CORS and response bounds; overload, SQL timeout, native SQLite interruption, disconnect and stalled-worker slot ownership. The unreadable-data test now simulates `PermissionError` instead of depending on the old release remaining inaccessible.

Independent full-snapshot SQL verification compares the original pre-extraction Python analysis and the extracted CLI with SQL for nine established cases. It checks exact selected IDs, all normalized term counts/ranking order, yearly/age/gender counts and valid/missing ages. All **987 raw pages** were rehashed; source pins and database bytes were unchanged. Means use absolute tolerance **1e-10 years** or relative tolerance **1e-12**.

Actual HTTP verification adds **23 selections**: those nine cases, twelve seeded raw-substring/year fixtures, a literal-plus case and a Unicode casefold input. All overviews match the independent original-Python reference. Concatenating every report page reproduces the exact sorted selected IDs: **1,530 page requests**, including all **97,652 IDs** in the overall case. **56 sampled details** agree on retained fields, normalization, ages, gender and raw product-match flags. Provenance/retained-field validation is additionally exhaustive in the offline preflight. The serving/benchmark source hashes match that HTTP parity run; only the permission-error regression test changed afterward.

| Representative selection | Matching reports | HTTP parity |
| --- | ---: | --- |
| All years, no product filter | 97,652 | Pass |
| 2024 only | 3,367 | Pass |
| Raw SUSPECT name contains CARROTS | 241 | Pass |
| 2024-2026 and CARROTS | 149 | Pass |
| Raw SUSPECT name contains VITAMIN D3 | 278 | Pass |
| No matching raw product | 0 | Pass |
| Literal percent / underscore / plus | 734 / 2 / 1,811 | Pass |
| Actual partial 2026 | 24 | Pass |

No search tokenization, wildcard substitution, trimming of a nonblank search, alias-based search substitution, normalization/counting/age/gender policy change or manufactured raw field was introduced. Missing ages remain counted reports. Raw matching determines which suspect products enter filtered product rankings; selected reports retain their reactions/outcomes. The preserved CLI fixture checks also compare grouped/empty text and PNG output with the original CLI.

The upstream suite's historically recorded three stale argument-test expectations remain unresolved: they omit the existing `groupBy: None` field. This slice does not claim that suite is green or republish its ignored tests. Those upstream tests were not rerun or edited here; the tracked local compatibility tests independently pass.

## Serving-Field and Size Preflight

The offline preflight checked all **97,652** retained details/summaries and source positions, not just example rows. It also tested the 100 largest summaries together with the maximum permitted product text and full bookmark allowance.

| Check | Result |
| --- | ---: |
| Largest actual report ID | 15 UTF-8 bytes; limit 512 |
| Largest detail with maximum-size filter text | 15,199 bytes |
| Largest 100-summary page with worst-case text/bookmark allowance | 17,741 bytes |
| Largest actual generated bookmark | 323 characters; limit 2,048 |
| Public metadata / compact prepared default | 1,808 / 4,230 bytes |
| Maximum allowed encoded data response | 1,048,576 bytes |
| Offline scan | 10.67 seconds; 49.37 MiB peak resident memory |

The release's formatted `saved-overview.json` is 12,806 bytes; its compact HTTP representation is 4,230 bytes. Runtime model/size checks remain active. Values are never silently truncated to satisfy a limit.

## Final Constrained HTTP Performance

**The approved warm default goal passes locally:** p95 **302.46 ms**, strictly below 10,000 ms, with **50/50 successful requests** from five clients.

The final installed package ran from outside the checkout. A separate server process was constrained by Windows Job Objects to approximately **0.1 CPU core** and **512 MiB committed memory**. Read-back CPU rate was 45/10,000 on 22 logical CPUs; five-second calibration measured **0.106 CPU seconds per wall second**. A temporary idle-sleep request was restored on exit. This is a desktop approximation, not proof of any provider's current resource allocation or Linux scheduling.

Each main scenario has **ten closed-loop waves of five clients**, after warmups. Each request opens a new local HTTP connection. Timing starts before client-task submission and ends after the complete response body arrives: dispatch/scheduling, actual HTTP/server handling, per-request connection setup, SQL, validation, encoding and loopback transfer are included. p95 is nearest rank; maximum is reported separately. Response JSON parsing by the benchmark client is outside the timed interval.

| Scenario | Successful / total | Median ms | p95 ms | Maximum ms |
| --- | ---: | ---: | ---: | ---: |
| Exact prepared default | 50 / 50 | 3.01 | **302.46** | 304.18 |
| Repeated uncached all-year CARROTS | 50 / 50 | 4,119.61 | **4,168.33** | 4,174.45 |
| Mixed uncached selections | 50 / 50 | 2,959.86 | **3,540.59** | 4,125.01 |
| Defaults mixed with uncached selections | 50 / 50 | 571.83 | **1,762.09** | 1,768.55 |

Mixed uncached fixtures are CARROTS, VITAMIN D3, literal `%`, no-match text, and 2024-only. The mixed-with-default scenario has two defaults, CARROTS, literal `%`, and 2024-only. Each main five-client scenario had no busy/error responses. No general cache exists, so these SQL results are recomputed every time; there is no result-cache eviction policy to exercise. Ordinary SQLite/OS page caching remains possible and is part of warm measurements.

Additional bounded diagnostics:

- Twenty simultaneous SQL requests: **5 successful, 15 explicit `503 SERVICE_BUSY`**. Successful-only p95/max was **3,583.04 ms**; all-response p95 was **3,574.96 ms**. Rejected work is not counted as successful query performance. This burst is not a sustained-arrival or traffic-flood test.
- Five default readers during five active SQL jobs: **5/5 successful**, p95/max **464.64 ms**. The background SQL requests also all succeeded, p95/max **4,153.91 ms**. These five-observation diagnostics are small samples, not separate guarantees.
- A real TCP disconnect was observed and signalled to the worker; shutdown ended with **zero active SQL jobs**, peak **five**. Deadline/slot-retention regressions separately use shortened test deadlines to avoid waiting 30 seconds per test.
- Peak server resident memory: **120,123,392 bytes / 114.56 MiB**, including startup and this run's work. The configured 512 MiB committed-memory cap remained active, but peak resident memory is not a measurement of peak commit or total container memory. The client/oracle/preparation processes are separate and not included in this serving-process figure.
- No scientific/analysis-policy imports in the server. Database bytes and all fifteen measured backend Python files were unchanged during the profile and matched the workspace afterward. The benchmark server exited successfully, with no server errors in its saved log.

The default-only ten-second goal is the user's hard latency criterion. The other figures are measured results, not a new promise that every possible filtered query will finish below ten seconds. Earlier SQL/runtime profiles used different paths and conditions; these are not controlled before/after speedup claims.

## Reproduction and Evidence

Commands and local URLs are in the [README](../README.md). Runtime pins are in `backend/requirements.lock.txt`, test pins in `backend/requirements-test.lock.txt`; the build uses setuptools 80.9.0. CPython **3.14.2**, SQLite **3.50.4**, Windows 11 x64 were used. The final local wheel is `project_lab_api-0.1.0-py3-none-any.whl`, SHA-256 `0190ce06967ce335d7d8f3c3407e73e6e989ca4f8e8c1b1590d346b89830d960`. Installed backend files were checked against the workspace. These are local environment/working-tree pins, not a CI/container or dependency-supply-chain guarantee.

Ignored local evidence under `generated/backend/`:

- `release/preparation.json`: rebuild, identity, byte counts and preparation resources.
- `verification/results.json`: original/current Python parity, all-page hashing and unchanged-source/database audit.
- `api-oracle.json`, `http-acceptance/results.json`: independent 23-selection reference and complete HTTP page/detail/overview checks.
- `preflight.json`, `api-tests.json`: exhaustive serving bounds and twelve API regression results.
- `http-constrained-final/results.json`, `server.json`, `server.log`, `openapi.json`: accepted final HTTP sample, resource/admission/disconnect outcomes, schema and code hashes.
- Earlier `http-constrained`, `http-unconstrained` and `http-final-parity` runs remain historical diagnostics, not substituted for the final numbers above.

Generated databases, wheels, benchmark output, build output and virtual environments remain ignored. No commit, push, repository publication, FDA-source change or portfolio change was made for this slice. The supplied baseline plan is unchanged.

## Limitations and Next Step

Local acceptance does not cover browser rendering, internet transfer, a sleeping service waking up, actual hosted resources, cold/restarted-process latency, growing arrival queues, deployment compatibility, public abuse resistance or every possible search. Readiness and same-release bookmark behavior were tested across app restarts; restart/wake-up performance was not benchmarked. SQLite cancellation is cooperative; noncooperative filesystem/native stalls cannot be instantly killed, and the slot is deliberately retained until exit.

The pinned Windows builder can still publish a private directory; readability must be checked before use. Starlette emitted a test-client `httpx` deprecation warning; the pinned tests pass, but future dependency updates require review. The upstream test-publication question, new-snapshot/policy/schema review process, container/CI reproducibility, and current $0 provider eligibility/limits remain separate work. No provider was provisioned or rechecked here.

**Stop for review before Slice 4.** The practical next implementation is the React/TypeScript/D3 MVP consuming this contract: shared selection state, aggregate views with accessible tables, report pages/details, saved-snapshot labeling and honest loading/error/stale-response behavior. Do not add more caching, cursor signing, a job queue or a general plugin framework without a demonstrated need. Frontend authorization and later $0 deployment review remain separate decisions.

These are FDA adverse-event reports, not unique people, causation, incidence, relative risk or product-safety conclusions. The completion/teaching/resume/Flex reminders remain pending until the agreed feature is genuinely finished and verified end to end.
