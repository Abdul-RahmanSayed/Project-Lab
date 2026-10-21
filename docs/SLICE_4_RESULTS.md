# Slice 4: Local Frontend Results

Completed locally October 20, 2026, within the [approved scope](SLICE_4_SCOPE.md), starting from Abdul's checkpoint commit `088ba1a3fcf3e74ca6ac6f4291beaa70948545df`. **The local React/TypeScript/D3 MVP passes. The deployed end-to-end feature is not complete.** No deployment, accounts, publication, commit, push, FDA-source edit or portfolio edit was performed for this slice.

## What Works

- One committed year/raw-product selection shared by all aggregate views. Draft text does not send requests; Apply preserves nonblank text exactly, including spaces, punctuation, case and Unicode. Reset also clears unapplied drafts.
- Five views: actual-year report counts, the existing 126 one-year age bins, and suspect-product/outcome/reaction rankings. React owns all DOM/SVG and D3 supplies scales. The three rankings use a shared zero-based count scale, with exact labeled values and overlapping-term caveats. Initial ranking charts show ten terms with the remaining prepared terms available; table mode exposes the complete returned rankings.
- Exact-value HTML tables for every chart; totals, valid/missing ages, nullable means and reported-gender context. January 1, 2026 is visibly marked as a partial year. The browser performs no second normalization, report aggregation, age conversion or alias-based search.
- Deterministic report pages, sizes 25/50/100, Next/Previous/First, and on-demand retained details with raw product roles, matching flags, canonical terms and source position. At most 100 prior bookmarks are stored, not result pages. Missing raw fields are disclosed, never fabricated.
- Overview, Reports and Snapshot & methods tabs; hash-backed exact filters, release, tab and page size; back/forward/reload, invalid-link repair, and copied view links. No localStorage, IndexedDB, user accounts or general result cache.
- A release-bound saved default while connecting or unavailable. An initial custom view receives no unrelated saved default. Previous results can remain only under their actual displayed-selection label and a previous-result indicator.
- Bounded metadata connection attempts, then manual retry; no automatic SQL retry/polling. Aborted superseded requests, generation guards against noncooperative late loaders, runtime schema validation, and exact response-context checks. Busy, unavailable, timeout, request-limit, no-match, invalid and release-mismatch states remain distinct.
- Responsive layout, container-measured chart geometry, wrapped labels, keyboard-operable tabs/tables/controls, native modal focus containment/Escape/return, touch controls, and reduced-motion support. Charts are the evidence-bearing visual assets; no marketing hero or decorative media was added.

The frontend is under `web/`; its [guide](../web/README.md) documents installation, build, tests and request/state ownership. The existing backend and its five-job/no-pending-queue/30-second resource policies are unchanged.

## Checked Data and Build

The public bundle was exported through the existing API's full release validation, not by inventing a new data-preparation path. It includes only public metadata, the exact prepared default, OpenAPI, generated TypeScript and an artifact inventory. No SQLite database or raw report pages are in the frontend.

- Release: `fda-release-sha256:18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194`.
- Database SHA-256 remains `bdfd771ede151a2784a83ff1e9ba1faad727491cce2bddf73a0499521b4d475f`; no database or analysis-policy change.
- Default: **97,652 reports**, **73,819 valid ages**, **23,833 missing/invalid ages**, mean age displayed as **48.29 years**. January 1, 2026 remains **24 actual 2026 reports**, not reassigned to 2025.
- Formatted frontend default **11,928 bytes**, public metadata **2,172 bytes**, OpenAPI **42,039 bytes**. The compact API default remains **4,230 bytes**. Formatting/source-envelope differences do not redefine the saved selection.
- Build checks artifact byte hashes/default identities, regenerates TypeScript from OpenAPI, typechecks and compiles. Export and a narrow `.gitattributes` rule pin LF endings for these new generated JSON files so Windows/Git conversion does not break their hashes. Existing pinned builder files are untouched.
- The line-ending-only export was rebuilt and the compiled JavaScript was verified byte-identical to the browser-tested build: SHA-256 `83c7e355a9e95aa8a86e07757b20355295f17cc034099a3de1470d58ef866c17`.

The saved default is validated at build/start and eligible only for its exact filters/release. A different API release is rejected with an explicit mismatch; no newer dataset is silently adopted. New snapshot/policy/schema changes still need a separately reviewed pin/rebuild and a matching frontend bundle.

## Verification

**The initial checkpoint passed build/typecheck, 17 unit checks and 21 production-preview browser checks**, with zero skipped/unexpected/flaky browser cases. The portfolio styling follow-up below reran build/typecheck, all 17 unit checks and 22 browser checks. Two focused report-dialog/touch regressions also passed in hot-reload development mode at the initial checkpoint; these repeat existing cases, not two additional unique tests. The temporary development helper was stopped; the compiled local preview remains available.

Unit coverage: raw text and URL round trips, Python-compatible code-point/UTF-8 bounds, invalid/reversed years, malformed/unknown/duplicate/wrong-release links, exact filter identity, UTF-8 BINARY report-ID comparison, bounded bookmark history, generated response schemas, incorrect/missing/extra response fields, response-context mismatches, streamed size bounds, proxy HTML and no automatic busy-query retries.

Actual browser/API coverage uses the existing checked backend and compiled frontend:

- Default counts and five rendered views; nonblank SVG data marks, consistent shared ranking scales and partial-year annotation.
- 2024-2026 CARROTS: **149 reports / 123 valid ages**, with annual counts **122 / 27 / 0**. Every annual/histogram table value and every canonical ranking label/count/order agrees with the same API selection, including the 126 age bins.
- Raw literal `%`, `_` and `+` searches return **734 / 2 / 1,811** reports. No-match is zero with unavailable means, not a network error. Typing alone does not query; whitespace-only search is rejected.
- Server-side pages: 25 rows, Next/Previous back to identical IDs, page-size reset to 100, then the remaining **49** rows for the 149-report case. Retained detail and provenance load; Escape/close returns focus to the originating report control.
- Back/forward, reload, tab selection, invalid URL repair, exact copied filters/release/tab, keyboard skip/tab navigation, and source/policy identities.
- Desktop **1440x1000**, mobile-width **390x844** and **320x740**, plus resize to **960x720**: no horizontal document overflow; plots remain contained and do not duplicate. Default/full-page, viewport and filtered mobile screenshots were inspected. A touch-enabled mobile-emulation context also applied filters and opened/closed report details.

Controlled browser fixtures deliberately test cases that are not claims about actual FDA data or a real provider:

- A loader that ignores cancellation returns an old selection after a newer response; the generation check prevents it overwriting the new selection. Previous values retain their original labels while waiting.
- No-valid-age and hostile raw-text cases preserve null means and render text without executing HTML.
- Busy, request-limit, timeout and release-mismatch errors do not replace previous values with zero/default data, and SQL work is not automatically retried.
- A default response deliberately returned for a filtered request fails exact context validation instead of being relabeled.
- Metadata unavailability stops after three bounded attempts in the production build; the default stays labeled and custom queries stay unavailable. A custom shared URL during mismatch/outage never receives the unrelated default overview.

The prior Slice 3 independent original-Python parity, 41 backend/core tests and constrained five-client HTTP evidence remain separately recorded, not presented as freshly rerun frontend measurements. This slice leaves the backend code unchanged and verifies the browser against its actual contract. It does not rerun all original Python analyses or the constrained backend profiler.

## Size and Local Browser Diagnostics

Pinned package installation uses Node **24.13.0**, TypeScript **5.9.3**, React **19.3.1**, D3 **7.9.0**, Vite **8.3.4** and Playwright **1.64.1**. npm's lockfile records transitive versions/integrities. TypeScript 5 was selected to satisfy the OpenAPI generator's supported peer range, without forcing dependency resolution. Installed Chrome was **155.0.8059.85**, on Windows 11.

The pre-alignment build had **485,997 bytes JS**, **15,283 bytes CSS** and a small HTML entry. Vite's estimated gzip sizes were approximately **147.09 kB JS / 3.96 kB CSS / 0.38 kB HTML**; this does not assert that the local preview or eventual host actually negotiates those encodings. The current styled build sizes are recorded below. There are no CDN runtime/font requests or bundled raw report datasets.

One pre-alignment local desktop navigation with the API warm observed the default success/mark-ready check at **565.5 ms** after the navigation time origin, **800 DOM nodes**, **181 data marks**, and approximately **11.3 MiB** of Chromium-reported used JavaScript heap. These are single diagnostic observations, not p95, paint timings, a leak/peak-memory test, whole-browser/process RSS, five-browser concurrency, container memory or hosted performance. They must not be combined with the historical backend p95 as an end-to-end SLO.

The only existing hard latency gate remains the approved warm default p95 below ten seconds for five requesters. Slice 3 met it for local HTTP under desktop constraints. This slice does not claim new hosted/browser p95 acceptance or impose a ten-second target on every filter.

## Portfolio Styling Follow-Up

Requested and completed locally October 20, 2026. Read-only references were the production portfolio's `artifacts/portfolio/src/index.css`, `components/Navbar.tsx` and related components in `Abdul-RahmanSayed.github.io`. The root Vue app is not the reference. No portfolio files were edited or built, and this is not portfolio integration or deployment authorization.

- Uses the same default near-black background (`hsl(240 25% 6%)`), dark surfaces, violet primary hue and mint secondary accent. Controls/tabs use violet; annual/product marks use mint; ages, outcomes, reactions and warnings retain distinct colors. Dashboard sections remain unframed and compact, not a copied marketing layout. No extra theme setting or framework was added.
- Inter and JetBrains Mono normal Latin variable faces are bundled from pinned Fontsource **5.3.0** packages, not requested from Google Fonts at runtime. System fallbacks preserve other Unicode glyphs; raw text and search semantics are unchanged. Two WOFF2 files total **88,660 bytes**, with OFL notices included in the compiled output. [Fontsource's variable-font guidance](https://fontsource.org/docs/getting-started/variable) documents this package-based approach.
- Text/control contrast is deliberately stronger than the portfolio's subtler decorative borders. The filled primary button uses a slightly darker violet for white-label readability. Measured default semantic text pairs are at least **4.98:1**, control border/surface is **3.32:1**, and chart mark/background pairs are at least **8.19:1**. These focused checks are not a full accessibility certification.
- Rebuilt/typechecked; **17/17 unit tests and 22/22 production-preview browser tests pass**, with zero skipped/unexpected/flaky browser cases. The added case checks the actual theme, both loaded local fonts, contrast pairs and themed table/report/dialog views. Existing parity, raw punctuation, selection/release identity, stale/offline/error, paging, keyboard and touch cases still pass. Desktop **1440**, mobile **390/320** and **960** resize checks remain contained without document overflow. Overview, table, methods, report, dialog and unavailable-state screenshots were inspected, including mobile overview/dialog views.
- Current build: JS **485,997 bytes**, CSS **16,271 bytes**, fonts **48,256 + 40,404 bytes**. Estimated gzip remains **147.09 kB JS**, with **4.20 kB CSS**. The JS SHA-256 is still `83c7e355a9e95aa8a86e07757b20355295f17cc034099a3de1470d58ef866c17`, byte-identical to the prior tested application logic. CSS SHA-256 is `6f8011c37637db7881f61eb1eec40f11066ebdf02ef58d7db79ad380d3002806`. Saved public data, the API and database were not rebuilt or changed for styling.
- One new warm local desktop observation, now also waiting for fonts, was **581.7 ms** to the success/mark-ready check, **800 DOM nodes / 181 marks**, and **9,286,833 bytes** of reported used JS heap. This is still a single diagnostic, not a controlled speed/memory comparison, p95, peak memory or hosted acceptance. No SQL/resource profiler was rerun for this CSS/font-only change.

The latest ignored evidence now includes `theme-check.json`, refreshed `unit-results.json`/`e2e-results.json`, browser diagnostics and `screenshots/portfolio-*.png`. The checked local preview serves this build. No provider/account eligibility review, provisioning, publication, deployment, portfolio edit, FDA-source edit, commit or push occurred. The separately authorized $0 deployment review must still test actual origin/version compatibility, fallback, wake-up and rollback; local styling does not complete those checks or trigger the completion reminders.

## Evidence and Reproduction

Use the [workspace README](../README.md) and [frontend guide](../web/README.md). Keep the checked backend at port 8765; the verified compiled preview is `http://127.0.0.1:4173/`. Vite's local proxy is only local development/preview wiring, not the future static-host/API-origin configuration.

Ignored evidence under `generated/frontend/`: `e2e-results.json`, `dev-smoke.log`, `browser-1440.json`, `browser-390.json`, `browser-320.json`, Playwright output and `screenshots/`. Generated build output/node_modules remain ignored. The small reviewed public bundle, generated API types, source and npm lockfile are intentionally tracked candidates; no staging or commit was performed.

Design references: [D3's React ownership guidance](https://d3js.org/getting-started#d3-in-react), [React effect cleanup](https://react.dev/reference/react/useEffect), and [Vite's local proxy configuration](https://vite.dev/config/server-options.html#server-proxy). The project-specific API/analysis policies remain defined by the checked local contract and FDA core, not those frontend references.

## Limitations and Next Step

Local browser/API verification is not deployed end-to-end completion. No provider eligibility or current free-resource limits were checked; no accounts or resources were provisioned. Internet latency, HTTPS/CORS across real origins, sleeping-service wake-up, production base paths, deployment compatibility and quotas/rollback remain untested. The UI handles simulated rate limits, not a measured provider quota. Cancellation is requested but cannot promise immediate termination of every proxy/native/filesystem operation.

Browser testing used Chrome with responsive/touch emulation, not physical phones, native on-screen keyboards, Safari/Firefox, or a real screen reader. Semantics/keyboard/touch paths were checked; this is not WCAG certification. Browser resource measurements are diagnostic, not a capacity guarantee. Reproducibility remains local-runtime/working-tree evidence, not CI/container/supply-chain verification. The upstream stale-test/publication issue and pinned Windows builder's publication-permission issue remain as documented in Slice 3.

**Stop for Slice 4 review.** The next separately authorized slice is the $0 deployment/portfolio integration review and implementation: verify current provider/account terms and resource limits before provisioning, then test real origin/version compatibility, fallback, wake-up and rollback. Do not provision, publish or change the portfolio based on this local result alone. Additional filters/parallel coordinates or another project are not silently added to the MVP.

FDA adverse-event reports are not unique people, causation, incidence, relative risk or product-safety conclusions. Completion/teaching/resume/Flex follow-ups remain pending until the agreed feature is genuinely complete and verified end to end.
