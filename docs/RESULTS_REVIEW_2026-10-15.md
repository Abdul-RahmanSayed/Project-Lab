# Results Review Before API Design

Reviewed October 15, 2026 (America/New_York). Evidence was measured October 9; this review is not a new benchmark or test-suite run.

**Assessment: Share with caveats. The evidence supports a documentation-only API contract draft, not API readiness or deployment.**

## Findings First

1. **Current release access blocks fresh verification.** Reading the previously selected release's release.json now returns access denied. A read-only retry outside the sandbox also failed; PowerShell confirms the path is inaccessible. Its cause was not established. No permissions were changed and no data was rebuilt. A readable, checked release and a successful integrity/parity run are prerequisites for API acceptance tests.
2. **The latency claim is correctly limited to encoded bytes.** The saved default p95 is reproducible from the 25 primary records, but does not include ASGI/HTTP, transfer, rendering, restart, wake-up, or open-ended arrivals. The gate cannot be promoted to a hosted guarantee.
3. **Cancellation/admission and pagination are implementation gaps, not tested features.** The current runtime performs synchronous SQL with no cancellation hook or bounded application queue. selected_ids fetches all selected IDs for verification; it is not a public pagination implementation. A naive async route calling that SQL directly could block the event loop. The draft contract requires separate worker ownership, bounded admission, deadline accounting, and keyset paging.
4. **The prepared database is a projection, not complete raw reports.** Products retain raw names/roles/positions plus canonical links. Ages and gender are derived; reactions/outcomes retain distinct canonical terms. Original raw reaction/outcome strings, raw age/unit values, and arbitrary raw JSON cannot be promised by a detail endpoint without a separately reviewed preparation change.
5. **Small samples and resource differences remain material.** The complete controlled run has 25 requests per workload; only three default requests occur in its mixed workload. It is closed-loop and not an overload/queue-growth test. Windows resident/committed memory and approximate CPU quotas are not Linux/container accounting. Connection-per-request filtered timings cannot establish a controlled speedup over earlier persistent connections.
6. **Reproducibility and publication are unfinished.** The source lock describes a local FDA working tree. Historical nine-case parity and 29 passing local tests are retained as dated evidence, not fresh claims. Three upstream tests still have stale groupBy expectations; upstream test-publication scope, CI/container reproducibility, and current provider eligibility remain unresolved.

No arithmetic discrepancy was found in the reviewed benchmark claim.

## Checks Performed Today

- Read the baseline plan, current decisions, implementation, schema, runtime verification evidence, controlled profile, and standby evidence.
- Independently sorted the primary default latency samples and selected nearest-rank p95 at ceil(0.95 * 25) - 1 = index 23: **2.0833 ms**, matching the recorded value.
- Rehashed runtime.py, profile_runtime.py, query.py, and windows_limits.py. All four still match their hashes in the controlled profile.
- Confirmed the working tree already contains the prior uncommitted performance follow-up; it was preserved.
- Inspected the serving schema for which fields are retained. Direct database shape/maximum-length checks could not run because release access failed.
- Checked current official FastAPI, Starlette, Pydantic, Python SQLite, and HTTP documentation for contract design. No backend dependency was installed.

The current p95 criterion remains **strictly less than 10,000 ms for the warm default all-year overview with five simultaneous requesters**. Maximum latency is diagnostic. The user has not set a new hard threshold for every arbitrary filtered query.

## Recorded Results, Not New Measurements

| Primary controlled workload | Requests | p95 |
| --- | ---: | ---: |
| Prepared default | 25 | 2.0833 ms |
| Repeated uncached carrots | 25 | 9,504.5492 ms |
| Mixed uncached SQL | 25 | 8,914.3472 ms |
| Mixed including defaults, all requests | 25 | 8,309.1893 ms |

Recorded process peak is 76.63 MiB, with a 4,230-byte prepared payload and a 59.27 MiB database. The original report's qualifications still apply. Two longer standby-affected runs are retained and excluded as uninterrupted warm-service estimates; the primary recorded interval had no observed sleep-entry events. Today's review did not reread the live Windows event log.

## Review Disposition

Proceed to the [FastAPI contract draft](FASTAPI_CONTRACT.md) as a design artifact. Do not create routes, install backend packages, build a frontend, run a service, provision resources, commit, or push as part of this task.

Before implementation acceptance: restore or deliberately regenerate a readable checked release without altering source policy, rerun integrity/parity, approve the proposed transport/queue/cursor limits, then test real ASGI handling and resource/cancellation behavior. A new checked release is required if pinned query/schema/preparation code changes; do not patch an existing database in place.

## Evidence

- [Measured follow-up and limitations](PERFORMANCE_FOLLOWUP_RESULTS.md).
- [Current user decisions](FDA_EXPLORER_DECISIONS.md).
- [Unchanged baseline plan](FDA_DASHBOARD_PLAN.md).
- Local ignored evidence: generated/performance/profile-constrained-controlled.json, verification/results.json, verification/sql-parity/results.json, and standby-evidence.json.
- Recorded checked release identifier: fda-release-sha256:18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194.

Hosting must remain $0. FDA reports do not establish unique people, causation, incidence, relative risk, or product safety.
