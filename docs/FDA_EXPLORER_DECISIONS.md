# FDA Explorer Decisions

This records later user decisions without rewriting the original baseline plan or historical measurements. When requirements conflict, the latest explicit user decision governs.

## October 9, 2026: Performance Expectations

The two-second five-client target in the baseline plan was provisional, not an original CLI requirement, a correctness condition, or a hosting restriction. The original CLI performance requirement concerned a single invocation. The web concurrency test was an additional planning check.

The user accepts a relatively long wait provided the default, all-year overview achieves **warm request latency p95 strictly below 10 seconds with five simultaneous requesters**, while the application fits the available free computing power, memory, and storage. Hosting must remain **$0**. The previous two-second target is no longer a required acceptance threshold; do not pursue it at the expense of scope or unnecessary complexity.

The user explicitly clarified that the acceptance statistic is p95, not the maximum: **p95 < 10,000 ms**. Measure individual request response times under five-client concurrency, not the sum of five response times. Record individual completions, median, p95, and maximum for diagnosis, but a maximum above ten seconds alone does not fail this latency criterion. The user did not set a new hard threshold for every arbitrary filtered selection. Keep measuring those cases and flag severe delays, without silently imposing the old two-second target on them.

Service wake-up remains a separate, previously accepted condition, with a clearly labeled saved overview. A warm-request benchmark does not include wake-up. Future API/frontend measurements must include request handling, serialization, queue wait, and rendering/network context as appropriate; local SQLite-only tests do not prove actual hosted behavior. The real selected free host's limits must be verified before deployment. Earlier memory/payload targets are planning headroom, not provider limits or newly imposed user requirements.

### Existing Evidence

The final Slice 2 constrained default-overview measurements were median 10.10 seconds, p95 13.05 seconds, and maximum 17.20 seconds with five simultaneous readers. These remain unchanged historical results. The p95 of 13.05 seconds does not meet the revised p95-below-ten-seconds criterion; the maximum is diagnostic only. Other measured five-client cases had p95 below ten seconds. SQLite-only peak resident memory was 76.67 MiB; the database was 59.27 MiB. Neither measurement establishes that the whole eventual hosted application fits all provider limits.

### Recommended Next Step

Because this snapshot and its default filters are fixed, the versioned release already contains the complete default overview. First test reusing that prepared response for simultaneous default requests instead of recalculating it separately for each reader. Check release identity and labels; changing year/product filters must still return the correct selected result, never an unrelated default answer.

Profile this path under the same constraints and preserve filtered-query parity. This is a recommendation, not authorization to start another implementation slice, an API/frontend, or deployment. Existing Slice 2 correctness results and the three pre-existing upstream test-expectation failures are unaffected by the revised latency goal.

## October 9, 2026: Bounded Performance Follow-Up

The user subsequently authorized testing reuse of the prepared default overview, rechecking memory and parity, and measuring repeated and mixed uncached selections with queue wait included. Additional filtered caching or concurrency controls should be bounded if needed, with eviction and queued latency measured rather than hidden. No raw substring, normalization, counting, age, or interpretation policies may be weakened.

The implementation adds a local read-only runtime adapter, not an API. It stores only one prepared immutable default response; filtered selections are not cached, so there is no eviction policy or growing filtered-result cache to test. The same versioned database/release and canonical core are retained. Review the follow-up results before designing the modular FastAPI contract or proceeding to API/frontend slices. Hosting remains $0; no provisioning, deployment, commit, or push is authorized by this follow-up.

The [follow-up results](PERFORMANCE_FOLLOWUP_RESULTS.md) record a complete short controlled run: default p95 2.08 ms with five concurrent requesters, mixed uncached SQL p95 8.91 seconds, and process peak 76.63 MiB. All 29 local tests and nine full-snapshot parity cases pass. Two larger runs were affected by Modern Standby and remain in the evidence. This is local runtime acceptance, not an HTTP/browser or host guarantee; results review still precedes API contract design.

## October 15, 2026: Results Review and API Contract Draft

The user authorized reviewing the recorded results and designing the modular FastAPI contract, not implementing or deploying an API/frontend. The [review](RESULTS_REVIEW_2026-10-15.md) independently reproduces the saved 25-sample p95 of 2.0833 ms and confirms that all four measured code hashes still match. The current saved release folder is access-denied even on an approved read-only retry, so no fresh database validation, shape/size profiling, full parity or test-suite result is claimed today. Restore readable checked inputs before API acceptance tests; do not silently change permissions, policy, or data.

The [contract draft](FASTAPI_CONTRACT.md) defines public schemas, lifecycle/readiness, exact selections, release-bound prepared responses, deterministic report pagination, errors, bounded admission/deadlines and cancellation ownership. Proposed sorting, cursor transport/signing, length/page/response limits, HTTP/SQL capacity and resource deadlines require review; they are not new user-approved SLAs or implemented controls. The only current hard latency criterion remains warm default p95 <10 seconds with five simultaneous requesters. No runtime code, FDA source, database, portfolio, backend dependencies, service, account, deployment, commit or push was changed by this documentation task.

## October 20, 2026: Approved Smaller Local Backend

After requesting a plain-language explanation and checking for overengineering, Abdul approved the **smaller local backend slice**: restore/check the data, expose overview/report requests, add basic safeguards, and verify correctness, memory and actual web-request performance. The [approved scope](SLICE_3_SCOPE.md) and [implemented contract](API_CONTRACT_IMPLEMENTED.md) supersede the corresponding proposals in the October 15 draft.

The simpler choices are ordinary URL-encoded report IDs; unsigned, strictly checked next-page bookmarks; report ID ascending order; page sizes 25/100; five active SQL jobs with **no application pending queue**; a finite built-in server limit instead of custom HTTP admission; a 30-second total SQL-backed resource budget; and one exact-release/default prepared response without a general result cache or signing secret. Product/URL/bookmark/response bounds reject invalid or excessive input/output instead of truncating it. These are resource and interface decisions, not a new ten-second SLA for every filtered query.

The unchanged pinned builder reproduced the same checked release while the old directory was inaccessible. The new copy's inheritance was enabled on that directory only. Abdul later repaired the original with administrator ownership/inheritance commands; its database hash and full API startup validation now match the rebuild. No broader permission repair was performed. The pinned builder's future Windows publication permissions remain a separate reviewed change, not a silent policy/source repin.

The [Slice 3 results](SLICE_3_RESULTS.md) record 41 passing local tests, nine independent full-snapshot SQL/CLI cases, 23 passing actual HTTP selections with complete deterministic pagination, and exhaustive retained-field/size preflight. The final constrained five-client HTTP run measured default p95 **302.46 ms** (50/50 successful), repeated uncached p95 **4,168.33 ms**, mixed uncached p95 **3,540.59 ms**, and peak server resident memory **114.56 MiB**. A twenty-request SQL burst produced five successes and fifteen explicit busy responses; rejected requests are not presented as successful fast queries. All jobs finished and database bytes were unchanged.

The revised default-only goal passes for actual local HTTP within the measured desktop constraints. Provider resources, internet/browser behavior, wake-up, container/CI guarantees and sustained arrivals remain unverified. No frontend, deployment, account, publication, commit or push is authorized by this slice. Review these results before authorizing Slice 4; hosting must remain $0, and all raw search, normalization, counting, age and interpretation policies remain unchanged.

## October 20, 2026: Local Frontend Authorized

After making the preceding local checkpoint commit, Abdul explicitly authorized Slice 4 with the pasted scope: React/TypeScript/D3 consuming the checked API, shared selection state, aggregate views and accessible tables, report pages/details, saved-snapshot labels and honest loading/error/stale behavior. This is frontend authorization, not deployment authorization.

The [Slice 4 scope](SLICE_4_SCOPE.md) retains the existing five aggregate views and year/raw-product filters. React owns all DOM/SVG; D3 supplies chart geometry. Hash-backed committed filters/release/tab/page-size state and separate draft controls avoid a request per keystroke. Bounded readiness attempts, cancellation/generation checks and response identity validation protect selection truth. The frontend bundles only the checked public default/metadata/contracts, not the database or raw pages. No general cache, cursor signing, pending-job queue, new policy implementation or plugin framework was authorized or added.

The [local frontend results](SLICE_4_RESULTS.md) separate actual browser/API verification from controlled failure/race fixtures and from untested hosted behavior. Deployment, accounts, provider eligibility/limits, internet transfer, sleeping-service recovery, portfolio integration, commits and pushes remain outside Slice 4. Hosting must remain $0; completion/teaching/resume/Flex reminders remain pending until the agreed feature is genuinely complete and verified end to end.

## October 20, 2026: Portfolio Visual Alignment

Abdul requested that the local UI match his existing portfolio, while reiterating that $0 deployment/portfolio integration needs a separately authorized slice. Read-only inspection identified the production React app under `artifacts/portfolio`, not the legacy root app. Its default dark background, violet/mint accents and Inter/JetBrains Mono families now inform the Explorer's tokens, controls, tables and report dialog. The compact dashboard layout, semantic chart/alert distinctions and all data/selection/request behavior remain unchanged. Two pinned font packages supply self-hosted faces; no runtime font CDN or new theme framework was added.

The follow-up passed build/typecheck, 17 unit tests and 22 browser tests, including a new local-font/contrast check and desktop/mobile screenshots. It is a local styling update, not Slice 5 acceptance. No provider/account terms were rechecked, no provisioning/publication/deployment occurred, and the FDA source and portfolio were not edited. The next deployment review must still establish current $0 eligibility/resource limits and test actual origins, release compatibility, fallback, wake-up and rollback before claiming completion.
