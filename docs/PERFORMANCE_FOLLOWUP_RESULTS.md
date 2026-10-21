# Prepared Overview Performance Follow-Up

Measured October 9, 2026, local time. The user-authorized bounded follow-up is complete. **The default all-year overview passes the revised warm p95 < 10 seconds goal in the local five-client test.** This is not a deployed HTTP/browser or actual free-host performance guarantee. API contract design and API/frontend implementation remain after review.

## Changes and Scope

`data-build/runtime.py` validates the existing release once, checks companion hashes and the pinned query-code hash, and loads one encoded, immutable default response. Only the exact all-year/no-product selection reuses these bytes; it opens no SQLite connection and does not re-encode JSON per request. This is bounded to one **4,230-byte** payload, not a growing arbitrary-filter cache.

Changed selections continue through the existing `query.py` SQL path, with a read-only connection opened and closed per request. Raw literal suspect-product substring search, Unicode casefolding, reviewed normalization/aliases, distinct per-report counting, and age/gender policies are unchanged. Invalid filter values cannot take the prepared shortcut. Responses identify the release, acquisition time, applied selection, prepared-versus-SQL source, and explicitly state a saved data snapshot rather than live FDA data.

There is no filtered-response cache, TTL/eviction machinery, request semaphore, or in-flight coalescer. Eviction is therefore **not applicable**, rather than an unmeasured claim about a general cache. No additional mechanism was needed to achieve the default-only goal. No FDA source/core/data changes, portfolio edits, accounts, hosted resources, deployments, commits, or pushes were performed in this follow-up. The user-created Project Lab repository remains on development with these changes uncommitted.

## Parity and Tests

All **29 local tests pass**: the existing eight SQL/semantic and ten Slice 2 tests, plus eight runtime tests and three temporary sleep-request restoration tests. Tests cover shared immutable bytes without default SQL calls, no cross-request mutation, changed/empty/year/product selections, Unicode and literal punctuation, raw selection before aliases, invalid shortcut inputs, concurrent consistency, corrupt artifacts, changed query-code pins, and absence of scientific/policy imports at runtime. The Windows sleep guard is tested for restoration both normally and on failure.

Fresh full-snapshot verification ran both the current CLI and the independent original analyzer recovered from the pinned local Git revision. All nine cases pass for the new runtime layer, and the underlying SQL verification again compares exact selected IDs, all term counts/ranking order, top 25, annual/age/gender counts, valid/missing ages, and means with the existing absolute 1e-10 / relative 1e-12 tolerances. Every one of the 987 source pages was rehashed, and source/database/release artifact hashes remain unchanged.

The three pre-existing upstream argument-expectation failures remain an unresolved historical issue: they omit the existing groupBy: None key. This follow-up does not alter those tests or the FDA CLI; it does not claim a newly all-passing upstream suite.

## Primary Controlled Measurement

The primary run used five worker threads and **five waves per workload: 25 measured requests per workload, 100 total**. Each wave submits five requests together and waits for all five to complete before the next wave. Three preflight warmups were performed per selection. This is a small closed-loop diagnostic, not an unbounded arrival-rate or production SLO test. Nearest-rank p95 is used; maximum latency is diagnostic, not a second acceptance threshold.

Timing begins before executor submission and ends after obtaining the full encoded response bytes. It includes dispatch, barrier synchronization, scheduling wait, filter validation, SQL connection opening/closing where applicable, and response construction. Post-response hash checks are outside the timed response interval. All response hashes match preflight; independent oracle comparisons are performed separately.

| Workload | Samples | Median ms | p95 ms | Maximum ms | Wait p95 ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Repeated prepared default, five concurrent readers | 25 | 0.25 | **2.08** | 6.02 | 2.08 |
| Repeated all-year carrots, uncached SQL | 25 | 8,886.41 | **9,504.55** | 9,512.96 | 5.82 |
| Mixed uncached SQL selections | 25 | 5,387.56 | **8,914.35** | 9,485.99 | 21.69 |
| Mixed selections including prepared defaults, all requests | 25 | 5,362.41 | **8,309.19** | 8,337.97 | 4.53 |

Mixed uncached selections rotate through 2024, carrots all years, 2024-2026 carrots, vitamin D3, no match, literal percent/underscore, and the partial 2026 year. Mixed-with-default additionally includes the exact prepared overview. Within that last workload, the **three default requests** had maximum/p95 **4.54 ms**; the sample is too small for a reliable separate tail estimate.

Only the default workload has the user's hard latency threshold. The 8-10 second uncached-filter costs are disclosed, not silently judged against the old two-second target. Wait is included in request latency; this experiment does not hide time behind a semaphore. There is no application concurrency queue yet, so reported wait describes this test harness's dispatch/synchronization/scheduling, not a future API queue.

## Resources and Provenance

| Measurement | Result |
| --- | --- |
| Primary constrained process peak resident memory | **76.63 MiB** |
| Isolated runtime process peak, without oracle allocations | **37.46 MiB** |
| Encoded prepared response | **4,230 bytes**, one retained entry |
| Database | **59.27 MiB**, unchanged |
| Release validation/loading startup, constrained primary run | **1.83 seconds**, outside warm requests |
| Isolated unconstrained startup | **0.137 seconds** |
| Environment | Windows 11 AMD64; 22 logical CPUs; Python 3.14.2; SQLite 3.50.4 |
| Configured local limits | Windows Job Object CPU rate 45/10,000; 512 MiB process/job committed-memory cap |
| Five-second CPU calibration | **0.10735 CPU seconds per wall second**, approximately 0.1 core |

Resident memory is Windows PeakWorkingSetSize, including native SQLite allocations and profiling bookkeeping, not Linux RSS or complete container memory. Job committed-memory caps and resident measurements are different metrics. Local CPU scheduling/calibration is approximate and not identical to any provider's quota.

The release remains `fda-release-sha256:18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194`. The dataset, core policy, schema, database bytes, source lock, and SQL query hash are unchanged from Slice 2. Runtime implementation SHA-256 is `d31fc589e254c5de2336c5dae4bc22e3d8dd8d9532b0a0c31c6761b306551158`; profiling evidence records separate hashes for its harness and Windows helpers.

## Standby-Affected Runs

The first 100-request-per-workload run overlapped confirmed Modern Standby intervals. It recorded default p95 0.39 ms, but filtered maxima included 333.70 seconds and 984.43 seconds. The mixed-with-default aggregate p95 was 513.57 seconds. These raw values are retained, not discarded or attributed solely to SQLite.

A second 100-request-per-workload run requested system activity only. This machine still entered Modern Standby, including a battery-drain-budget transition. Default p95 was 3.82 ms, but the final mixed workload again contained a 598.47-second maximum. **That run is also not an uninterrupted warm-service estimate.** Earlier progress updates should be read with this later finding.

The primary shorter repeat requested both system and display activity while profiling. The Windows System log shows **zero Modern Standby entry events in its 20:13:10-20:15:44 EDT interval**. The request is restored on exit and does not change saved power settings or block deliberate user sleep; see Microsoft's [execution-state API](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate). The display requirement is a benchmark control, not application runtime behavior.

The two larger default-only phases also pass with 100 observations each, but their overall runs contain standby interruptions. The complete shorter controlled run is the primary mixed-workload evidence. Do not cherry-pick filtered observations from the interrupted runs or treat any small sample as a host SLO guarantee.

## Reproduction and Evidence

Commands are in the [README](../README.md). Use `--constrained --keep-awake`; `--rounds 5` reproduces the short primary diagnostic, while `--rounds 20` requests 100 observations per workload. Check power events if a run has unexpectedly extreme wall-time tails.

Ignored local evidence:
- `generated/performance/verification/results.json`: runtime/original-Python comparisons, response fingerprints, and isolated memory.
- `generated/performance/verification/sql-parity/results.json`: fresh full SQL/current/original parity and complete source rehash audit.
- `generated/performance/profile-constrained-controlled.json`: primary complete controlled run, raw timings, wait/service breakdowns, code hashes, and strict default gate.
- `generated/performance/profile-constrained.json` and `profile-constrained-awake.json`: retained larger, standby-affected runs.
- `generated/performance/standby-evidence.json`: power-event evidence and second/primary interval checks, including zero sleep-entry events 42/506 in the primary run.

## Limitations and Next Step

The prepared-default approach meets the revised goal **for the local encoded-response path** without a general cache or changed data semantics. HTTP/ASGI handling, internet transfer, rendering, cancellation, growing arrival queues, process restarts, service wake-up, and actual hosted resources are untested. The primary per-filter samples are small; mixed selections are representative fixtures, not every possible user search. SQL per-request connection setup also differs from the historical persistent-connection benchmark, so filtered timings are not a controlled before/after comparison.

Review these results, then design the modular FastAPI contract: response/provenance schemas, readiness and metadata, explore and deterministic report pagination, error/limit/cancellation behavior, and release-bound cache/concurrency policies if needed. Do not implement or deploy the API/frontend before that review. The prepared payload must change with the selected checked release, and must never answer a different filter selection.

Reproducibility remains pinned to this local runtime and FDA working tree, not a CI/container supply-chain guarantee. New snapshot/policy/schema versions need a separate reviewed pin/rebuild process. Upstream test publication/stale expectations remain unresolved. Provider eligibility and real free-resource limits have not been rechecked; no resources were provisioned. Hosting must remain $0. FDA reports are not unique people, causation, incidence, relative risk, or product-safety conclusions.
