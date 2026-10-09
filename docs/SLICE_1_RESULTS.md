# Slice 1 Results: Local SQLite Feasibility

Measured October 9, 2026. Slice 1 is complete. The prototype reconciles the existing saved FDA snapshot, agrees with the original Python analysis, and supports real local read-only filtering. This is evidence for continuing to Slice 2, not a hosted-service performance claim.

## Scope and Provenance

The supplied plan was copied unchanged to [FDA_DASHBOARD_PLAN.md](FDA_DASHBOARD_PLAN.md). The original and documentation copy have SHA-256 `d7fb2f293c490179fe297f46f8f17d610cf4c5e8b1754a68e75047fa6abee079`. [Assumptions](SLICE_1_ASSUMPTIONS.md) were stated before implementation.

| Identity | Verified value |
| --- | --- |
| FDA source revision | `6496e08754e428c87900c272ba61bcae86f2b9f5` |
| Actual `part2.py` SHA-256 | `cd46a46f61d5a2c2159c25251c1d81a055132f0d727b762e464ccd85b67f6dd8` |
| Completion manifest SHA-256 | `8a81a0be1fc8f22b1733e33edf3ca6a50256a772d2ebe5aa9e5fff6aed3f6862` |
| Snapshot identity SHA-256 | `2f7ab38cb063859ecc2ace39d7eda363cfd2e72996890a30dd5c71582a9b3f07` |
| Coverage | January 1, 2002 through January 1, 2026, inclusive |
| Acquisition completed | September 4, 2026, 18:29:41.824 UTC |
| Reconciled inventory | 987 pages; 97,652 reports; 97,652 unique report IDs |

The snapshot identity hashes the manifest hash plus the ordered page inventory containing relative paths, SHA-256 hashes, byte lengths, and report counts. It identifies these saved files, not an immutable upstream FDA version. Source policies and every manifest-listed page were checked again after verification. The database hash was also unchanged after queries. FDA Git status remained unchanged; the portfolio was not accessed or edited.

## Preparation and Memory

Environment: Windows 11, AMD64, 22 logical CPUs; Python 3.14.2; SQLite 3.50.4. Preparation/oracle dependencies are pinned in `data-build/requirements.lock.txt`: pandas 3.0.6, NumPy 2.5.3, Matplotlib 3.11.2, and their installed dependencies.

| Measurement | Result |
| --- | --- |
| Prepared database | 44,388,352 bytes / **42.33 MiB** |
| Preparation elapsed | **29.88 seconds** |
| Preparation peak resident memory | **117.63 MiB** |
| Isolated query-process peak resident memory | **50.09 MiB** |
| Original Python oracle batch peak resident memory | **432.96 MiB** |
| Original Python oracle batch elapsed | **20.48 seconds** across all nine cases |
| Query/benchmark process peak including parity allocations | 76.76 MiB |
| Compact overview JSON sizes | 1,790 to 3,860 bytes |

Preparation streams one page at a time. It calls the existing manifest/report validators and normalization, age, gender, and disclosure policies. Database constraints reject duplicate report IDs and repeated reaction/outcome memberships. Window totals, final totals, uniqueness, foreign keys, and SQLite integrity were checked before publishing the candidate file.

The preparation timer starts before policy import and covers provenance, page reading/hashing, validation, normalization, inserts, indexing, integrity checks, and publication of the candidate database. It excludes interpreter startup and final evidence-file writing/database hashing. Resident memory is the process-lifetime peak reported by Windows `GetProcessMemoryInfo` (`PeakWorkingSetSize`), including native allocations. Preparation, oracle, and runtime measurements use separate processes. The oracle reads all raw reports and builds pandas analysis results without generating PNGs; its batch elapsed time is not a complete CLI benchmark.

Prepared table counts: 97,652 reports; 157,159 raw product rows with original roles and names; 286,317 distinct report/reaction memberships; 139,832 distinct report/outcome memberships; 61,751 dictionary entries across products, reactions, and outcomes. Product memberships overlap and must not be summed as unique report counts.

## Python Parity and Warm Latency

All nine full-snapshot cases passed. Verification compared exact selected report IDs, all canonical term counts and ranking order, top-25 rankings, annual counts including zero years, all 126 age bins, valid/missing age counts, and gender counts. Total/female/male means passed absolute tolerance `1e-10` years or relative tolerance `1e-12`. Eight focused regression tests also passed, including Unicode casefolding, literal wildcard/punctuation search, aliases after raw selection, duplicate/overlapping memberships, ages 0/fractional/125/invalid, unknown gender, empty results, invalid ranges, and rejected read-only writes.

Warm latency includes the complete overview query and compact JSON encoding: one sequential read-only connection, 8 MiB configured SQLite page cache, three warmups per case, 30 measured iterations, no result cache, and nearest-rank p95. Full ID/all-term oracle comparisons are outside the timed interval. The machine was not CPU- or memory-constrained; these are desktop measurements.

| Selection | Python = SQLite reports | Valid ages | Median ms | p95 ms | Maximum ms |
| --- | ---: | ---: | ---: | ---: | ---: |
| Overall, 2002-2026 | 97,652 | 73,819 | 1,592.80 | **1,739.13** | 1,755.69 |
| 2024 only | 3,367 | 2,720 | 42.88 | **51.72** | 52.42 |
| Raw product contains `cArRoTs`, all years | 241 | 160 | 695.59 | **787.02** | 793.03 |
| 2024-2026, raw product contains `CARROTS` | 149 | 123 | 42.89 | **52.48** | 53.60 |
| Raw product contains `VITAMIN D3` | 278 | 240 | 668.66 | **765.27** | 789.17 |
| No-match product text | 0 | 0 | 627.40 | **752.75** | 792.11 |
| Literal `%` | 734 | 414 | 712.80 | **776.74** | 810.28 |
| Literal `_` | 2 | 2 | 632.82 | **722.97** | 3,392.25 |
| January 1, 2026 only | 24 | 20 | 2.22 | **3.40** | 4.11 |

Overall mean age is 48.29269326687743 years, female mean 50.58016984408065, and male mean 42.471368183729375. Invalid/missing ages account for 23,833 reports and remain in overall totals. Empty selection has null means, empty rankings, and zero-filled year/age counts.

The observed 3.39-second underscore outlier is retained in the results. Its cause was not isolated. Thirty sequential observations cannot establish performance under load or a reliable tail-latency guarantee.

## Demonstrated Filtered Query

```powershell
.\.venv\Scripts\python.exe -B data-build\query.py --database generated\slice1\fda.sqlite3 --start-year 2024 --end-year 2026 --product CARROTS
```

Result: **149 reports**, **123 valid ages**, **26 invalid/missing ages**, mean age **42.94996883747072** years. Annual counts are **122 in 2024**, **27 in 2025**, and **0 in 2026**. Python produces the same result. Only matching raw suspect products enter the product ranking; all reactions/outcomes of the selected reports remain eligible.

The query process imports no pandas, NumPy, Matplotlib, or FDA policy module. It opens the prepared database using SQLite `mode=ro`, also enables `query_only`, and passes filter values as parameters. Raw product search uses Python `casefold()` and SQLite `instr()` rather than SQL wildcard search; see the official [URI reference](https://www.sqlite.org/uri.html) and [scalar-function reference](https://www.sqlite.org/lang_corefunc.html).

Local artifacts, all ignored: `generated/slice1/fda.sqlite3`, `preparation.json` with the full page hash inventory, `oracle.json`, `queries.json`, `runtime.json`, combined `results.json`, and `filtered-example.json`. Reproduction commands are in the [workspace README](../README.md). No Git repository has been initialized; `.gitignore` is ready for later source control.

## Limitations and Next Step

- This is a local query/database prototype, not a FastAPI service or stable public contract. The temporary explicit-checkout policy adapter is limited to preparation and verification. Policy packaging, release/schema migration rules, saved default overview, and runtime readiness belong to Slice 2.
- Counts/rankings and means agree for the tested cases; this does not prove every future filter, pagination rule, or response schema. No API/UI, multi-client concurrency, cold-start, constrained CPU, deployment image, or hosted-memory measurement was performed.
- The overall p95 is close to the plan's provisional two-second target on this desktop. SQLite currently materializes the selection separately for each aggregate. Literal substring searches inspect candidate product rows, including when no match exists. Query plans use `reports_year` and product membership primary keys; optimize repeated selection/aggregation and reassess full-range queries before service readiness is claimed.
- The isolated query peak is substantially below the oracle peak, but FastAPI/deployment overhead and concurrency have not been included. The later 350 MiB/five-client budgets remain unverified. Preparation belongs offline, not on a request or service wake-up.
- No provider eligibility or current hosting limits were rechecked. The $0 spending constraint, sleeping-service allowance, and clearly labeled saved overview remain requirements. Accounts, provisioning, payments, publishing, and portfolio integration remain outside this slice.
- This saved snapshot ends January 1, 2026; 2026 is not a complete year. Report mentions are not unique people, causation, incidence, relative risk, or product-safety conclusions.

Recommended next step: review these results, then authorize **Slice 2** to package the canonical validation/policy core while preserving the FDA CLI, harden reproducible database preparation and versioning, build a labeled saved default overview, and reduce repeated selection work. Recheck parity and profile under constrained resources before progressing to the FastAPI/API and frontend slices. No further slice has been started.
