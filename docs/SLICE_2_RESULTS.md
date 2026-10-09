# Slice 2 Results: Shared Core and Versioned SQLite

Measured October 9, 2026. Slice 2 implementation and correctness acceptance are complete. The constrained five-client latency target used at measurement time was **not met**. No FastAPI/API, frontend, hosting, account creation, publication, commit, or push has started.

**Later user decision, October 9:** the provisional two-second target is superseded by **warm request latency p95 strictly below ten seconds** for the default all-year overview with five simultaneous requesters, within available free computing power/memory/storage. The measurements below are unchanged historical evidence. The default p95 of 13.05 seconds does not meet the revised goal; maximum latency is diagnostic, not a separate acceptance threshold. See [current decisions](FDA_EXPLORER_DECISIONS.md).

## Scope and Assumptions

The unchanged [baseline plan](FDA_DASHBOARD_PLAN.md) remains the architectural baseline. Slice 1's [results](SLICE_1_RESULTS.md) are historical, not rewritten by this slice. The user's Slice 2 authorization permits a narrowly scoped core extraction in the FDA repository while retaining its CLI.

- The current validated snapshot remains fixed: 987 pages and 97,652 unique reports; no downloads or automatic refresh.
- The user confirmed January 1, 2026 intentionally belongs to the final 2025 download window. Analysis still uses actual report dates: 24 reports are in 2026, which covers only that single day.
- Raw suspect-product substring search, reviewed normalization/aliases, per-report distinct counting, disclosure labels, and age/gender rules remain canonical.
- Preparation happens offline. A sleeping $0 service and an explicitly labeled saved default overview remain acceptable; local profiling does not prove any host's eligibility or performance.
- Only the authorized core/CLI/package files change in FDA. The portfolio, downloader, saved raw data, source README, ignored upstream tests, and review notes remain unchanged.

## Implemented

FDA owns a standard-library-only, installable `fda-analysis-core` 0.1.0 package, split into policy, validation, and errors. `part2.py` reexports the existing names, preserves source-local default paths and CLI behavior, and retains the scientific analysis/plotting layer. Plotting imports are deferred until chart work; importing the core needs none of pandas, NumPy, or Matplotlib.

Project Lab builds a pinned wheel from a temporary copy without leaving packaging artifacts in FDA. A normal rebuild requires the existing source lock and rejects a changed wheel or build metadata. The lock pins the base Git revision **and exact uncommitted file content**, core version/hash, wheel SHA-256, and saved snapshot. Verification recovers the original analyzer from the pinned local Git revision, rather than requiring old generated Slice 1 evidence.

Preparation uses the installed package, not an explicit-checkout policy adapter. It hashes the exact page bytes it parses, exhausts canonical manifest/report/window/count/uniqueness validation, enforces database constraints, runs integrity/foreign-key checks, and rehashes pages, source, and builder code before publication. Incomplete, duplicate, changed, or corrupted inputs fail closed.

Schema version 2 retains raw names, roles, and canonical links; adds distinct suspect-product memberships, covering indexes, and annual aggregates. Default/year-only selections use those prepared totals. Product-filtered overviews materialize and reuse the selected set in one aggregate statement; full-range raw product matches are computed once and reused in rankings. Short year ranges search year candidates. Raw literal casefolded substring search remains unchanged, including literal `%` and `_`; no wildcard, fuzzy, tokenized, or canonical-name substitution was introduced.

An entire release is staged, checked, and atomically published to a content-derived directory. It includes the database, metadata, page inventory, labeled saved overview, and artifact checksums. A differing release cannot overwrite an existing identity; previous releases remain usable. Timings are outside deterministic release content. Query opening uses read-only mode plus query-only enforcement and rejects unsupported schema/hash identities. A future service must validate the complete bundle at startup, not merely open the database.

## Provenance and Reproducibility

| Identity | Verified value |
| --- | --- |
| FDA base Git revision | `6496e08754e428c87900c272ba61bcae86f2b9f5` |
| Source kind | Local working tree; only part2.py modified among previously tracked source files, plus new core/package files |
| Snapshot SHA-256 | `2f7ab38cb063859ecc2ace39d7eda363cfd2e72996890a30dd5c71582a9b3f07` |
| Core policy SHA-256 | `a89dcc5c5961f7d7e5b8af99ea9a9ecc8dee4b4abd12e70feae25d66e604a282` |
| Schema version / SHA-256 | 2 / `8041ae142dc15cf658a7a8c4bcd24594a7577e70ad8b2223a87a697bed5cd17b` |
| Release SHA-256 identifier suffix | `18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194` |
| Database SHA-256 | `bdfd771ede151a2784a83ff1e9ba1faad727491cce2bddf73a0499521b4d475f` |
| Core wheel SHA-256 | `891cd476d58190e42fecaab2ccc94761c6d49488fbef7f3ca1fd49ddcbdafb46` |
| Snapshot acquisition completed | September 4, 2026, 18:29:41.824 UTC |
| Coverage | January 1, 2002 through January 1, 2026 inclusive |

Two independent final database builds have identical bytes and identical release artifacts, including metadata, saved overview, page inventory, and release manifest. Two independently rebuilt final wheels also have identical bytes; a third rebuild passed the strengthened pin check. This proves reproducibility for the pinned local environment, not across arbitrary SQLite/Python/build-tool versions.

Environment: Windows 11 AMD64, 22 logical CPUs, Python 3.14.2, SQLite 3.50.4, setuptools 80.9.0. Preparation and verification dependencies are pinned in `data-build/requirements.lock.txt`; the core and query path use only the standard library. Release identity includes source lock, dataset/policy/schema identities, builder/query hashes, and Python/SQLite versions. A policy, schema, snapshot, or builder change requires a new checked release; existing databases are not mutated or migrated in place.

## Preparation, Memory, and Size

| Measurement | Final result |
| --- | ---: |
| Database bytes / MiB | 62,152,704 / **59.27 MiB** |
| First preparation elapsed / peak resident memory | **13.68 seconds / 54.19 MiB** |
| Independent second build elapsed / peak | **13.19 seconds / 54.27 MiB** |
| Isolated query process peak | **38.71 MiB** |
| Five-client constrained process peak | **76.67 MiB** |
| Compact live-query overview JSON | 1,921 to 3,987 bytes |
| Saved default overview JSON, formatted and labeled | 12,806 bytes |

Preparation timing includes validation, page hashing/rehashing, normalization, indexes/aggregates, integrity checks, release artifacts and validation, and publication. It excludes interpreter startup and writing the outer timing record. Peak resident memory is Windows GetProcessMemoryInfo PeakWorkingSetSize, including native allocations. Separate preparation/oracle/query processes avoid confusing scientific-library overhead with runtime memory. These are not Linux RSS or whole-container measurements.

The larger database trades 16.94 MiB over Slice 1 for prepared suspect memberships, annual aggregates, and covering indexes. Preparation peak fell from 117.63 to 54.19 MiB. Table counts reconcile 97,652 reports, 157,159 raw products, 112,385 distinct canonical suspect memberships, 286,317 reaction memberships, 139,832 outcome memberships, and 61,751 dictionary entries. Product/reaction/outcome memberships overlap and must not be summed as unique reports.

## Parity and Desktop Warm Latency

All nine full-snapshot cases passed against both the freshly run extracted CLI and the freshly run original analyzer from the pinned pre-extraction revision. Comparison covers exact selected IDs, all normalized term counts and ranking order, top 25, annual/age/gender counts, valid/missing ages, and total/female/male means. Means use absolute tolerance 1e-10 years or relative tolerance 1e-12. Every manifest-listed page and source policy was rehashed; queries left database bytes unchanged.

The 18 Project Lab tests passed: eight focused SQL/semantic tests and ten core/CLI/release tests. Coverage includes numeric normalization and non-alias neighbors, all age units, fractional/zero/125/invalid ages, missing/unknown genders, Unicode/literal punctuation, duplicate/overlapping terms and IDs, invalid manifests and malformed JSON including CR newlines, rejected writes, unsupported schema hashes, atomic/reproducible preparation, corrupt/incomplete release inventory, and mismatched package pins. Five fixture CLI cases also produced identical text summaries and identical PNG bytes before/after extraction, including grouped and empty cases.

The unchanged upstream Python suite has **28 passes and three pre-existing failures**, reproduced before and after extraction. Three argument tests omit the already-existing `groupBy: None` key from expected dictionaries. They were not changed or silently treated as passing. The local independent compatibility tests preserve the actual existing contract.

Desktop timing: three warmups, 30 measured iterations per case, one sequential read-only connection, 8 MiB configured SQLite page cache, full overview plus compact JSON encoding, no result cache, nearest-rank p95. Oracle/ID/all-term comparison work is outside the timing interval.

| Selection | Reports | Valid ages | Median ms | p95 ms |
| --- | ---: | ---: | ---: | ---: |
| Overall, 2002-2026 | 97,652 | 73,819 | 61.68 | **72.04** |
| 2024 only | 3,367 | 2,720 | 4.01 | **6.18** |
| Raw product contains carrots, all years | 241 | 160 | 50.63 | **56.15** |
| 2024-2026 and CARROTS | 149 | 123 | 52.79 | **59.80** |
| Raw product contains VITAMIN D3 | 278 | 240 | 56.01 | **69.86** |
| No-match raw product | 0 | 0 | 46.22 | **53.60** |
| Literal percent sign | 734 | 414 | 58.34 | **70.87** |
| Literal underscore | 2 | 2 | 51.46 | **55.21** |
| Actual 2026 year, January 1 only | 24 | 20 | 0.71 | **1.42** |

For context, Slice 1 desktop p95 was 1,739.13 ms overall, 787.02 ms for all-year carrots, and 752.75 ms for no match. These separate local runs demonstrate a substantial observed improvement, not a controlled-host speedup guarantee. The combined 2024-2026/carrot case did not improve in this run (52.48 ms in Slice 1 versus 59.80 ms now); the optimized query shape is not universally faster.

The demonstrated filtered result is unchanged: 149 reports, 123 valid ages, 26 missing/invalid ages, mean age 42.94996883747072 years, annual counts 122 in 2024 / 27 in 2025 / 0 in 2026. Only matching raw suspect products enter product rankings; all reactions/outcomes of selected reports remain eligible. Empty results retain null means, empty rankings, and zero-filled year/age/gender arrays.

## Actual Resource-Limited Profile

The profiler applied a Windows Job Object hard CPU cap and 512 MiB committed-memory caps to its own process only, read the limits back, and ran a five-second CPU calibration. Rate 45/10,000 on 22 logical CPUs yielded **0.09979 CPU seconds per wall second**, approximately 0.1 core. The cap pauses the job after its scheduling-interval budget is consumed; it is not identical to Linux/container or hosted scheduling. See Microsoft's [CPU rate control](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information) and [committed-memory limits](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_extended_limit_information).

Sequential: three warmups and five measured requests per case. Concurrent: five threads, independent read-only connections, three warmups per connection, synchronized start, five measured requests each (25 observations per case). Each case repeats the same selection without response caching. Latency includes overview and JSON encoding, not HTTP/network/client overhead. With five sequential observations, nearest-rank p95 is the maximum; these small tests are diagnostic, not an SLO guarantee.

| Selection | Constrained sequential p95 ms | Five-client p95 ms | Five-client maximum ms | Two-second target |
| --- | ---: | ---: | ---: | --- |
| Default overview | 588.37 | **13,053.94** | 17,204.95 | **Fail** |
| 2024 only | 2.79 | **1,195.84** | 1,767.33 | Pass in this small test |
| All-year carrots | 612.46 | **5,337.08** | 5,340.38 | **Fail** |
| All-year no match | 590.75 | **4,759.83** | 5,326.34 | **Fail** |

Peak resident memory was 76.67 MiB, below the provisional 350 MiB process budget **for this SQLite-only process**. Payload size passes the 250 KiB budget. Five-client latency fails despite serial latency passing. No FastAPI, ASGI server, deployment image, Linux memory accounting, cold starts, or actual hosted resources are included. The older intermediate constrained run also failed the broad-query concurrency target; its exact timings are not the final release measurements.

## Saved Overview and Local Evidence

The release's `saved-overview.json` contains the actual default query, not placeholders: label **Saved overview / data snapshot**, `isLive: false`, acquisition time, release/dataset/policy identities, applied 2002-2026/no-product filters, all overview aggregates, and coverage/interpretation notes. It has 97,652 reports, 73,819 valid ages, and 23,833 missing/invalid ages. Overall mean age is 48.2926932668774 years. This is a prepared fallback artifact only; no UI, loading state, wake-up handling, or HTTP serving was built.

All local artifacts are ignored. The accepted final bundle is under `generated/slice2/final-release-a/18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194/`; its identical independent copy is under `final-release-b`. Final parity evidence is `generated/slice2/final-verification/results.json` with separate current/original oracles and a filtered example. Final constrained evidence is `generated/slice2/profile-final-constrained.json`. Pinned wheels are under `package-final`, `package-final-b`, and `package-lock-checked`. Reproduction instructions are in the [workspace README](../README.md).

Project Lab remains an ordinary local folder, not an initialized/published repository. Its ignore rules cover generated data, databases/journals, environments, and bytecode. No source-control actions occurred. FDA git diff whitespace checks pass. Existing unrelated untracked files in FDA were left alone.

## Limitations and Recommended Next Step

**Stop here before the API/frontend slices.** Slice 2's policy, CLI compatibility, deterministic preparation, independent parity, and labeled saved artifact acceptance are met. The revised default-overview performance goal is recorded separately; the original two-second threshold is no longer required. No new implementation has started.

Updated recommendation: first test reusing the already prepared default overview under the revised p95-below-ten-seconds expectation, rather than separately recalculating an identical answer for each reader. If additional runtime caching or concurrency controls are needed, keep them bounded and measure both repeated and **mixed uncached selections**, including queue wait and cache eviction; a semaphore alone does not remove queued latency. Do not silently weaken raw substring search or normalization/age/count semantics. Recheck memory and parity after changes, then design the modular FastAPI contract once the requirements and results have been reviewed. The user has not set a new hard latency threshold for every filtered query.

Current reproducibility is pinned to this local runtime and working tree; it is not yet a CI/container supply-chain guarantee. New snapshots and policy/schema revisions need a separate reviewed pin/rebuild process. The upstream test-publication/stale-expectation question remains unresolved. Current hosting/provider eligibility was not rechecked, and no resources were provisioned. Hosting must remain $0. This saved data describes reports, not unique people, causation, incidence, relative risk, or product-safety conclusions.
