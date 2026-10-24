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

## October 20, 2026: Slice 5 Hosting Review Authorized

Abdul authorized starting the next slice with provider/account/resource review and a concrete proposal **before** provisioning, publication or portfolio changes. He confirmed that he has no Render account and is willing to make Project Lab public if that simplifies deployment. No account was created and no repository visibility was changed. The configured GitHub remote returned 404 through public and connected metadata reads; accessibility/visibility is unresolved, not assumed private or public.

The [Slice 5A proposal](SLICE_5_DEPLOYMENT_PROPOSAL.md) recommends GitHub Pages, one Render Free API built from a reviewed Dockerfile/commit, and the existing checked database as a checksum-pinned GitHub Release attachment outside Git history. Current official documentation was reviewed, including separate workspace/compute costs, free CPU/RAM, idle wake-up, bandwidth/build allowances, suspension and rollback limits. Render account-specific verification remains untested; stop if a payment method or paid plan is required. Alternative Docker Spaces/Koyeb signup terms did not meet the proposed new-account $0 path.

This phase added documentation only. It rechecked database bytes/size, inspected existing origin/binding/retry wiring and recorded planned Linux/hosted checks; it did not rerun parity/performance/browser suites or establish hosted acceptance. The deployment proposal, artifact publication and portfolio integration need their relevant approvals before execution. No new filters, caching framework, job queue, snapshot/policy repin, FDA-source edit, provision, deployment, account, commit or push occurred. Completion follow-ups remain pending.

## October 20-21, 2026: Local Deployment Preparation Approved

Abdul explicitly approved packaging the checked release, adding container/API-origin
wiring and testing locally, while excluding accounts, resources, publication,
repository visibility changes, portfolio edits, commits and pushes.

[Slice 5B](SLICE_5_LOCAL_PREPARATION_RESULTS.md) records the checksum-pinned archive,
candidate Docker context/runtime, deployment app entry point, trusted HTTPS frontend
origin and local tests. Final checks passed: 12 preparation/configuration, 12 API,
20 frontend unit, 22 existing browser and four separate-origin HTTPS cases. The
HTTPS API ran an isolated installed wheel, and real stop/restart tests recovered
through manual Retry without changing data/filter labels. All test helpers stopped.
SQL admission/deadlines and raw search/normalization/age/counting policies are unchanged.

Docker/Podman and an installed WSL runtime were unavailable. No Linux image was
built or accepted; compatible wheel downloads and an actual base digest are not
execution/security proof. Linux parity/resources and real hosted eligibility,
origins/certificates, idle wake, quotas and rollback still require verification.
No new latency/peak-memory claim, external action or completion reminder follows
from this local preparation result.

## October 21, 2026: Accounts and Local Linux Follow-Up

Abdul provided the GitHub URL, and connected repository metadata now confirms
Project-Lab is public with default branch `development`. He reports creating a Hobby
Render account, removing its initially attached card, and installing Docker Desktop
and WSL2 himself. This is not authorization for service creation, publication,
portfolio changes, commits or pushes; account-specific billing/resources have not
been independently inspected.

The [Linux follow-up](SLICE_5_LINUX_RESULTS.md) built the unchanged candidate image
and tested the existing release with 0.1 CPU/512,000,000-byte limits, no swap and
read-only/non-root execution. Eleven Python-reference overview fixtures and bounded
report/detail checks passed. Default HTTP p95 was 26.62 ms for 50/50 successful
requests; process high-water resident memory was 105.88 MiB and container-accounted
peak 206.20 MiB including cache/inspection work. Repeated/mixed uncached batches,
overload and same-image restart were measured without adding caching/queues or
changing search, normalization, ages or counting. Small filtered samples establish
no new universal latency target.

This removes the missing-local-Linux-runtime blocker, not the public-runtime
security/currentness review or hosted acceptance. The retained Python/Bookworm base
was not silently upgraded. Source/history review, actual no-card/Free eligibility,
publication/provision approvals, real origin/version/fallback/wake/rollback and the
separately approved portfolio edit remain ahead. Completion reminders stay pending.

## October 21, 2026: Local Runtime Refresh Authorized

After the publication/runtime review, Abdul authorized only a small local runtime
and build-tool refresh, preserving the exact database and policy/query pins and
repeating correctness/resource checks. Both Docker stages now pin the inspected
Python 3.14.8/Bookworm amd64 digest; builder pip 26.2.2 and setuptools 84.2.1 wheels
are hash-pinned. Neither is importable from the venv or base interpreter in the final
serving filesystem. No framework upgrade, distribution migration, new snapshot,
data repack/rebuild or API/query/policy implementation change was introduced.

The [refresh results](SLICE_5_RUNTIME_REFRESH_RESULTS.md) record 12 existing API
regressions on Linux/Python 3.14.8, 11 HTTP parity fixtures and repeated/mixed
uncached resource measurements. All 12 invariant file hashes stayed fixed;
25 installed application source files matched the workspace. Default p95 was
76.84 ms for 50/50 requests under 0.1 CPU/512,000,000-byte limits; server resident
high-water memory was 100.87 MiB and container-accounted peak 108.13 MiB. These are
local observations, not a controlled speed/memory improvement over the older run.

The review's maintenance items are addressed locally, but complete native/OS
advisory coverage and hosted acceptance remain unestablished. No deployment,
publication, service/account creation, portfolio edit, commit or push is authorized
by this refresh. $0/account checks and explicit approval still precede public steps;
actual origin/version/fallback/wake/rollback and completion reminders remain pending.

## October 21, 2026: Public Hosting and Archive Authorized

Abdul confirmed Hobby/no-card/no-services and supplied the unused usage allowances,
then explicitly authorized one Render Free backend, Pages publication and bounded
hosted tests. After discussing openFDA reuse and unresolved third-party terminology
questions, he chose to continue and separately approved a public checked archive.
This is authorization to proceed, not legal or universal security clearance.

The [partial hosted results](SLICE_5_HOSTED_RESULTS.md) record the actual account
checks, published checksum-matching attachment and first Free API deployment from
`db52f77`. Persistent auto-deploy and PR previews are off; readiness is `/readyz`.
Eleven overview fixtures and bounded report/detail parity passed over actual HTTPS.
The warm default returned 50/50 successes at p95 169.06 ms, maximum 190.52 ms.
Small repeated/mixed uncached batches passed, and ten concurrent SQL requests
produced five successes/five explicit busy responses. No data/policy/query pin,
semantic, cache, admission or deadline changes were made.

The initial new-check-client failure was a mistaken reference-metadata assumption,
not an application failure; it is retained separately from the successful run.
Abdul chose to make the narrow Pages-workflow/test commit and push himself. The
agent has not committed/pushed or changed the portfolio. Pages, actual browser
integration, provider resource observations, genuine idle wake and rollback remain
unfinished. Completion follow-ups stay pending until the agreed end-to-end feature
and separately approved portfolio integration are genuinely verified.

## October 21, 2026: Pages Published and Backend Restored in Rehearsal

After Abdul pushed `88430e7`, the manual Pages workflow successfully published the
explicitly selected `db52f77` application and unchanged checked release. Its public
manifest records the actual Render origin and selected code/data pair. Bounded real
Chrome default/filter/table/report/detail/shared-link/mobile-width checks passed.
Screenshot tooling failed, so complete hosted visual verification is not claimed.
One same-data deployment of `88430e7` and provider rollback to the original `db52f77`
deployment succeeded; an actual filtered browser request worked after restoration.
This tests infrastructure restoration, not a data migration. Subsequently the
original Pages deployment job successfully republished its existing artifact and
the public manifest retained the compatible code/API/data pair. The exact public
website files are retained locally with checksums; this is not a differently
versioned frontend rollback or indefinite provider artifact retention.

Render Free gates application memory/CPU charts behind a paid upgrade. No upgrade
was made and no hosted peak-memory claim substitutes earlier local measurements.
Genuine idle sleep/wake, remaining fallback/visual evidence and
the separately approved portfolio integration remain open. The detailed evidence
and small-sample limitations are in the hosted results; the MVP is not complete.

After over 18 minutes without agent API requests, one timed readiness request
returned the correct release in 12.69 seconds. Browser automation disconnected
during the idle wait, so the provider's asleep state and actual cold-browser
fallback/recovery were not verified. This is a single idle-period observation,
not a warm-default p95 failure, completed wake-up gate or measured browser load.

## October 21, 2026: Bounded Memory Log and Browser Recovery

Abdul requested restored browser access and a small opt-in memory log, without
paid tooling. The deployment launcher now supports Linux `FDA_MEMORY_LOG=1`, off
by default, with at most 200 request samples plus startup/graceful shutdown. It
records only counters and release/process context, with unavailable counters
marked unknown. It adds no endpoint, dependency, timer, cache or queue and does
not change data, policy, query, admission or deadline behavior.

Nine focused tests pass on Windows and installed Linux; all 12 existing Linux API
regressions and bounded independent-reference HTTP parity pass. Under local
0.1 CPU/512,000,000-byte constraints, logged cgroup peak was 130.02 MiB and warm
five-reader default p95 was 85.74 ms (50 successes). These are local measurements
with logging enabled, not Render memory evidence or an overhead comparison.
See [results and measurement limitations](SLICE_5_MEMORY_LOG_RESULTS.md).

Chrome restart/extension reopening and Render sign-in restored browser control.
Desktop screenshots now verify the default and report detail, plus an explicitly
labeled invalid-release saved-view state. The restored session's viewport override
did not apply, and neither natural sleep/wake nor actual hosted outage recovery
was proved. These limitations remain open rather than being inferred from local
tests or the dashboard's live-deployment badge.

Abdul retains commit/push ownership. The next diagnostic deployment requires his
pushed commit; it has not happened. Use only the existing Free service, restore
the log flag to zero after bounded measurement, and retain separate approval for
portfolio edits. The MVP and completion follow-ups remain pending.

## October 23, 2026: Resume Hosted Acceptance From Saved Evidence

The October 21 complete pushed revision `5a76fbe` was manually deployed to the
existing Render Free service with the approved bounded diagnostic enabled.
Deployment `dep-dbc825bbc2fs73bk2t50` succeeded. Its bounded HTTPS checks passed
all 11 parity fixtures and the warm default gate: 50/50 successes, p95 151.93 ms,
maximum 155.48 ms. Repeated/mixed uncached selections passed and the SQL burst
retained five explicit busy responses. Data/policy/query pins remain fixed.

Retained host logs show process RSS high-water 99.96 MiB and resolved cgroup peak
89.20 MiB against a reported 512 MiB group limit. These are different accounting
measures, not a full independent enforcement/OOM audit. The UI exposed 50 lines
ending at sample 127; its lifetime high-water counters include earlier work.
The [memory follow-up](SLICE_5_MEMORY_LOG_RESULTS.md) records exact values/limits.

The previous session stopped before confirming that the zero flag was saved and
applied to a restarted worker. Resume with that inspection/cleanup, then complete
sleep/unavailable browser recovery. No whole-suite rerun is implied by this
evidence review. Portfolio editing still requires the separate approval and
the MVP/completion reminders remain pending.

The resumed session confirmed the actual flag was still `1`, saved it to `0`
and applied the existing image as successful deployment
`dep-dbdretjrjlhs7384useg` (11.1 seconds). A fresh browser CARROTS request
returned 149/123/26. A short reversible suspension then verified actual hosted
default/custom/previous-result fallback. Resume initially left filtered routes
returning provider suspension HTML despite readiness; one service restart and
manual Retry restored the expected default, custom and empty selections. The
root cause of that provider routing inconsistency remains unknown.

New 390x844 viewport screenshots and report-detail scrolling checks passed, and
the override was reset. All FDA tabs were then closed for a single natural idle
trial beginning at 19:46:46.762 UTC. See the [recovery record](SLICE_5_RECOVERY_RESULTS.md)
for exact evidence, the distinction between outage and sleep, and pending gates.

The first trial showed saved-first browser recovery after an idle interval, but a
Cloudflare challenge on the command-line non-waking probe prevented affirmative
sleep evidence. One final trial used the normal browser for that probe. At
20:51:52.153 UTC it displayed Render's documented sleeping-service robots response
after 29 minutes 55 seconds without agent API traffic. The subsequent default
visit retained its labeled saved overview, was still Connecting at 14.159 seconds,
and API ready by the next observation at 46.671 seconds. A new CARROTS query then
returned 149/123/26. No manual Retry was needed for that particular cold visit.

This satisfies the bounded natural sleep/wake check, with observation bounds and
one-trial limitations kept separate from warm request p95. No more idle trials,
new cache/queue, retry changes or runtime implementation work is needed at this
milestone. The service is resumed, logging is off, the mobile override is reset
and the filtered demo is left open. The concrete two-field portfolio proposal is
documented for separate approval; final acceptance and completion reminders still
depend on that integration and verification. No portfolio edit, commit or push
was made by the agent.

## October 23, 2026: Approved Local Portfolio Integration

Abdul approved enabling the existing FDA Live Demo link and appending the exact
saved-snapshot Explorer sentence, with local checks only and commit/push retained
by him. The production React portfolio was clean on `master`; the local review
branch `codex/fda-explorer-link` now has only the two approved lines changed in
`artifacts/portfolio/src/components/ProjectsSection.tsx`. Existing attribution,
claims, source link, dependencies and publishing workflow are unchanged.

Frozen-lockfile installation, TypeScript checking and the production build pass.
Isolated desktop/mobile browser checks confirm the exact new anchor and sentence,
usable card/action layout and no page exceptions. Request recording with an FDA
blocking guard observed zero attempted Explorer/API requests during homepage
load, scrolling and link focus/hover; no link click was included in those tests.
See [portfolio results and limitations](SLICE_5_PORTFOLIO_RESULTS.md).

The public portfolio is not changed by this local work. After Abdul's reviewed
publication to its existing `master` deployment path, verify the real public link
and no-FDA-request homepage behavior before final acceptance. No additional FDA
runtime, data, cache, queue, deployment or account change is part of this step.
The MVP and completion follow-ups remain pending.
