# FDA Explorer and Reusable Project Lab

Planning date: October 8, 2026.

Status: proposed implementation plan, not an implemented or deployed feature. The user confirmed that an occasional approximately one-minute backend wake-up is acceptable if the interface immediately presents a clearly labeled saved overview.

## 1. Recommendation and boundaries

Build a separate, reusable Project Lab with a React/TypeScript/D3 frontend and a modular FastAPI backend. Start with an FDA Explorer backed by a prepared, read-only SQLite snapshot. Keep the existing portfolio as the lightweight entry point, and keep the FDA repository as the authority for ingestion and analysis policy.

Use GitHub Pages for the static demo frontend and provisionally use one Render Free web service for the Python API. Treat $0 as a spending constraint, not a promise of unlimited capacity or zero maintenance. Confirm account eligibility and actual limits before deployment. No accounts, repositories, branches, hosted services, or credentials have been created by this planning work.

Initial scope:

- Explore the existing saved snapshot, not continuously scrape the live FDA API.
- Execute real backend filtering, aggregation, and pagination.
- Preserve the existing CLI commands and their output behavior.
- Begin with year-range and raw suspect-product search; add more filters in a later verified slice.
- No authentication, uploads, writable application database, arbitrary-code execution, live ingestion endpoint, or job scheduler in the first release.
- Support desktop and mobile, keyboard use, shareable filter state, and a useful cold-start/offline experience.

## 2. Evidence inspected

### D3 reference

Read the ZIP directly without executing its scripts or extracting its embedded Git repository:

[Abdul_Michelle_lab6.zip](<C:/Users/abdul/OneDrive/Documents/Beedo/School/Gatech/Senior Year/Intro to InfoVis/Lab 6 Final/Abdul_Michelle_lab6.zip>).

Inspected the contained README, index.html, main.js, colors.js, style.css, dataset field notes, and CSV. The README starts a local static HTTP server; it does not describe an application backend. This review did not run the visualization in a browser or inspect the accompanying assignment PDF.

The CSV contains 3,770 rows, 29 countries, ten question dimensions, five demographic subsets, and three answer categories. There are 130 ':' missing-percentage values. The initial Lesbian/Yes selection contains 290 rows before missing-value handling.

What the actual code implements:

- Dropdown selection of demographic subset and answer category, plus a redundant Filter Data button.
- A country-level parallel-coordinate plot with a percentage scale from 0 to 100 on each question axis.
- Country-line hover highlighting, point tooltips, and enter/update/exit rendering.
- Suppression of a whole country line if a selected percentage is missing.

No axis-brushing or axis-reordering implementation appears in the inspected main.js. Those would be new features, not preserved functionality.

Preserve the interaction principles, not the old rendering structure:

| Reference detail | Consequence for the new implementation |
| --- | --- |
| Dropdowns drive one filtered selection | Use one typed filter state for all FDA views. |
| Hover emphasizes a selected country | Support hover, keyboard focus, and tap selection for groups/reports. |
| Fixed 1400 x 650 layout | Measure chart containers and use a separate mobile composition. |
| Tooltips and legend elements are appended inside every updatePlot call | Create these once through React ownership; prevent accumulating DOM nodes. |
| Axis key is d => d === d; point key returns the entire object | Use stable dimension IDs and stable report/group IDs. |
| Broad svg.selectAll('path') can include axis paths | Restrict D3 to explicit layers/ref-owned groups. |
| Implicit global points, shared globals, and d3.event | Use scoped TypeScript state and modern event arguments. |
| Missing data removes an entire country line | Make missing-data exclusions visible; never silently erase FDA reports from totals. |

The ZIP also contains an approximately 24 MB country GeoJSON and other resources not loaded by the inspected page. Do not carry them into FDA Explorer. Preserve Abdul/Michelle team attribution when describing the reference project.

### FDA pipeline

Inspected the local [README](<D:/Documents/Beedo/FDA-Food-Safety-Data-Pipeline/README.md>), [downloader](<D:/Documents/Beedo/FDA-Food-Safety-Data-Pipeline/part1.js>), [analyzer](<D:/Documents/Beedo/FDA-Food-Safety-Data-Pipeline/part2.py>), requirements, ignore rules, and completion manifest.

- The manifest reports 97,652 unique reports and 987 pages, covering January 1, 2002 through January 1, 2026, downloaded September 4, 2026.
- Current raw data occupies approximately 68.3 MiB across 988 files, including the manifest.
- part1.js already separates reusable ingestion functions from its CLI entry point and handles cursor validation, shared pacing, retries, duplicate IDs, and completion publication.
- part2.py already separates loading, selection, normalization, age conversion, rankings, grouped summaries, printing, and PNG generation into functions.
- However, main() reloads/validates the raw data, builds a DataFrame, and writes a chart on each invocation. Importing part2.py also imports pandas, NumPy, and Matplotlib.
- The README documents a 25.8-second full CLI run and prior validation results. Those are documented measurements, not fresh benchmarks from this planning session. No tests or full dataset reconciliation were rerun here.

Inspected the current portfolio workflow and app routing: only artifacts/portfolio is published to Pages. The current Express/OpenAPI scaffold describes a health endpoint, not an FDA service.

## 3. Architecture: separate preparation from interaction

```text
FDA repository                     Project Lab release process
-----------------------            ---------------------------
Node downloader                    Pin FDA source + snapshot version
        |                                      |
Raw pages + manifest -----> Validate + prepare SQLite database
                                  |                 |
                           Saved overview       API image
                                  |                 |
                           GitHub Pages          Render
                                  |                 |
Portfolio -- Live Demo --> React + D3 -- queries --> FastAPI
                                                    |
                                         FDA query module
                                         Future project modules
```

Preparation is an offline/build task. Serving visitor requests is a lightweight read-only task. Downloading the FDA dataset must never be triggered by a visitor opening the page, changing a filter, or calling a public API endpoint.

The prepared database is included in the deployment image. Startup checks its identity, schema, and readiness; it does not reconstruct it from all 987 pages. Use SQLite read-only connections with mode=ro, and do not modify the database in place during runtime. SQLite documents this connection mode in its [URI reference](https://www.sqlite.org/uri.html).

## 4. Repository ownership and future expansion

Recommended ownership, subject to approval before creation:

| Repository | Responsibility |
| --- | --- |
| Existing portfolio | Project descriptions, source links, Live Demo links. |
| Existing FDA pipeline | Raw snapshot, Node ingestion, canonical Python rules, existing CLI. |
| Proposed Project Lab | Demo frontend, shared API host, FDA web adapter, deployment, contract tests. |

Package/extract the FDA policy code in its existing repository and consume a pinned commit or version in Project Lab. Do not fetch and execute a floating GitHub branch at request time, copy the entire pipeline into the portfolio, or import modules through absolute paths on Abdul's computer.

Suggested Project Lab logical structure, not files created by this plan:

```text
apps/web/                       React application and project routes
apps/api/                       FastAPI application and shared middleware
apps/api/projects/fda/          FDA routes, schemas, and query adapter
apps/web/projects/fda/          FDA views and filter state
shared/contracts/              Generated API types and schema snapshots
data-build/                     Pinned source acquisition and preparation
deployment/                     Container and host configuration
tests/                          Platform/API/UI contract and regression tests
```

Use one modular API process initially, not one permanently running service per project. FastAPI supports namespaced project modules using [APIRouter](https://fastapi.tiangolo.com/tutorial/bigger-applications/).

Future projects register a title, slug, source URL, demo route/URL, backend requirement, and resource budget. Share layout, loading/error states, API client conventions, health checks, logging, and contract generation. Keep domain models and queries inside their project modules. Do not build a generalized plugin framework before a second project actually needs it.

Projects requiring another language, GPUs, heavy jobs, or persistent writes may use separate services or external demo URLs. The registry can include them without forcing them into the FDA backend. Modular growth does not guarantee that every future workload will fit a free tier; shared deployments also share CPU, memory, downtime, and failure risk.

## 5. Shared analysis core and prepared data

Extract policy and validation functions into importable Python modules without changing behavior. Keep part2.py as a compatibility CLI entry point. Retain existing imports/re-exports as needed for local tests and callers. Move plotting dependencies to the plotting/CLI path so the API does not load Matplotlib or pandas merely to answer a query.

Reuse the existing reviewed aliases, numeric-safe normalization, age factors, getGender behavior, manifest checks, and duplicate-report validation in the preparation stage. Do not invent a second normalization implementation in SQL or JavaScript.

Prepare these logical tables:

| Table | Purpose |
| --- | --- |
| snapshot_metadata | Dataset identity, source revision, coverage, acquisition time, preparation time, schema/policy versions, hashes, report count. |
| reports | One row per report ID, event date/year, converted valid age or NULL, normalized gender or Unknown. |
| report_products | Report ID, product role, raw name, Python-casefolded search text, canonical product key. Preserve raw-to-canonical relationships. |
| report_reactions | Distinct report ID/canonical reaction memberships. |
| report_outcomes | Distinct report ID/canonical outcome memberships. |
| term_dictionary | Stable keys, display labels, and disclosure notes such as EXEMPTION 4. |

Preserve only the approved public detail fields needed for the first release. Retain provenance that allows a record to be traced to its source page. Add indexes based on actual query plans and measured workload rather than indexing every column.

Important query rules:

- Raw product search remains Python casefold substring matching on SUSPECT products. Store folded text during preparation and casefold the input through the same Python policy. Ordinary SQLite lower()/LIKE is not an equivalent Unicode implementation; LIKE also treats '%' and '_' as wildcards unless handled. Start with a parameterized literal-substring predicate such as instr, then benchmark it.
- Select distinct report IDs before aggregating. Joining multiple product, reaction, and outcome tables directly can multiply rows and inflate counts.
- In a raw-product-filtered ranking, count only the matching suspect products, then deduplicate their canonical names per report. Retain all reactions/outcomes of selected reports, as the CLI does.
- Missing/invalid ages do not remove reports from totals. They are excluded only from age calculations unless an explicit age filter changes the selection.
- Gender Unknown remains inspectable; it is not silently removed.
- Preserve the one-year histogram bins, including fractional ages and exact age 125. Zero-count years remain present.
- Product-group memberships overlap. Never sum their counts or combine their means as though groups were disjoint.

Database-query outputs must match the CLI oracle on counts/rankings and use an explicit numerical tolerance for means. Identical normalized input does not, by itself, prove equivalent aggregation semantics.

## 6. API contract

Start with a small, read-only versioned contract:

| Endpoint | Response |
| --- | --- |
| GET /healthz | Process health only. |
| GET /readyz | Dataset/schema readiness; 503 when unavailable. |
| GET /api/v1/projects | Demo registry, available capabilities, and dataset versions. |
| GET /api/v1/fda/metadata | Snapshot coverage, source, supported filters, caveats, normalization version. |
| GET /api/v1/fda/explore | Consistent bundle: selected count, valid/missing ages, age means, annual counts, histogram, and rankings. |
| GET /api/v1/fda/reports | Bounded, stable pagination for the same selection. |
| GET /api/v1/fda/reports/{id} | Approved public detail fields and provenance. |

MVP filters: explicit startYear, endYear, and optional raw product text. Add age range, gender, canonical outcome/reaction selections, and grouped comparisons after CLI parity is established. Treat these as new functionality with a written policy, not capabilities the CLI already has.

All data responses carry datasetId, policyVersion, canonical appliedFilters, and relevant coverage notes. Means without valid ages are JSON null, never NaN/Infinity. Match ranking ties deterministically. Reject invalid ranges, unsupported filters/sorts, oversized strings, and unsupported snapshot IDs.

Use Pydantic response/request schemas and generate TypeScript types from the backend OpenAPI contract. Do not independently maintain a conflicting second hand-written API specification. The existing Orval approach can be reused if useful, but creating another Express proxy is not required.

Return one overview bundle per committed filter change rather than separate requests for every chart. Use bounded caching keyed by dataset/policy/filter versions and query settings. Pagination has a stable sort and a dataset/filter-bound cursor; do not permit a cursor to be reused for a different selection.

## 7. Frontend and visualization design

Analytical jobs: time change, distributions, category rankings, and report drill-down. Primary renderer: D3 scales/shapes with React-owned SVG. Use ref-owned D3 groups only where axes or brushing require imperative DOM manipulation. This follows the ownership distinction in [D3's React guidance](https://d3js.org/getting-started#d3-in-react).

Start with five aggregate views: annual counts, an age histogram, and three compact ranking charts for products, outcomes, and reactions. Each receives tens to hundreds of marks, not 97,652 report paths. Detail rows are paginated and load on demand. No Canvas/WebGL is needed initially; consider Canvas only if a later dense view earns it through profiling.

Reading order: dataset/source coverage -> active filters -> selected/valid-age counts -> time and age evidence -> rankings -> report details. Use a neutral context color, a clear selected accent, direct labels, and text equivalents; color alone must not encode selection or missingness. Place the partial-2026 annotation on the time view itself.

Interactions:

- Desktop: year/product controls first; later brushing converts a finished range into canonical filters. Hover/focus highlights details without sending requests.
- Mobile: single-column charts, collapsible controls, visible filter chips, tap/focus details, and numeric/select alternatives to dragging.
- Commit requests through Apply or a bounded debounce. Do not send a backend query on every brush pixel or keystroke.
- Abort superseded browser requests and accept a response only for the active filter/query version. Keep previous results visibly marked as updating; never relabel old numbers as though they answer a new filter.
- URL-backed committed filters, snapshot ID, selected tab, and sort. Defaults are omitted; invalid state produces a visible repair message. Hover and drag-in-progress state are not persisted. Shared URL state overrides personal defaults.
- Bounded query retries, no continuous polling/keep-awake traffic. Keyboard access, readable tables, reduced-motion behavior, and clear empty/error states are part of the first usable release.

Parallel coordinates are a second-stage group-comparison view, not the initial report-level visualization. Candidate axes: report count, valid-age coverage, and average age by selected year/gender/product group. Axis units and scales must be explicit; missing averages remain missing; product overlap is disclosed. Validate that these measures answer a useful question before adding the view. Offer a comparison table as its mobile/accessibility fallback.

Do not add a map: the reviewed ingestion/analysis contract has not established a usable geography field.

## 8. Cold starts and graceful degradation

Build a small default-overview JSON from the same prepared snapshot and publish it with the static frontend. It contains only the documented default selection, not a fabricated cache of arbitrary filters.

The page displays this immediately, labeled Saved overview / data snapshot, while attempting the API request. Distinguish starting, API ready, querying, unavailable, quota exhausted, and no-match states. Permit a bounded wake-up/retry window and a manual retry action. A single browser-tab retry flow should serve all charts, rather than five independent wake-up loops.

Until live queries are available, clearly explain that custom filtering is unavailable; do not let changed controls suggest that the saved numbers have been recomputed. Previously fetched results may remain visible only with their actual filters attached. A newer backend dataset must not silently mix with the bundled overview or old cached pages: identify versions and visibly reconcile or ask to reload the current view.

Saved preview does not replace the backend: successful interactive queries, public API docs, server-side pagination, validation, and observable response behavior are the showcase.

## 9. Free hosting and cost controls

Provider facts checked October 8, 2026; recheck before provisioning:

- Render Free sleeps after 15 idle minutes; waking takes about a minute. Its 750 monthly running hours are workspace-wide. Filesystem changes are ephemeral; free Postgres expires after 30 days. Bandwidth/build overages can incur charges with a payment method; without one, services/builds can be suspended. [Render free-tier documentation](https://render.com/docs/free).
- The current free web-service compute specification is 0.1 CPU and 512 MB RAM. [Render compute plans](https://render.com/docs/compute-plans).

Design response: one sleeping API process; immutable database in its image; no runtime persistence; no periodic wake-up pings; compact responses; bounded caches and concurrency. Prefer an account without a payment method where permitted and verify provisioning requirements. If a payment method becomes necessary, pause rather than assuming a spend limit blocks every category of charge. No paid add-ons or automatic upgrades.

GitHub Pages hosts the static frontend. For proposed public repositories, standard GitHub-hosted Actions runners can perform preparation/tests without runner charges; avoid larger runners, unbounded artifact retention, and assumptions that every Actions feature/storage is unlimited. [Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages), [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions).

Alternative if sleeping-service tradeoffs later become unacceptable: Cloudflare Workers plus D1 and the same prepared SQL model. It requires a different runtime adapter and quota-aware queries/imports, not a drop-in hosting switch. Current Workers Free limits include 100,000 daily requests, 10 ms CPU/request, and 128 MB memory; time awaiting a database is not CPU time. D1 Free has 5 million daily rows read, 100,000 rows written, and 500 MB per database. These constraints make offline preparation, indexes, and measured query costs important. [Workers limits](https://developers.cloudflare.com/workers/platform/limits/), [D1 pricing](https://developers.cloudflare.com/d1/platform/pricing/), [D1 limits](https://developers.cloudflare.com/d1/platform/limits/).

The primary recommendation remains Render/FastAPI because the confirmed cold-start tolerance permits the simpler standard Python runtime. No provider can be guaranteed free forever. Expansion must remain inside measured resource budgets or degrade/stop instead of spending automatically.

## 10. Maintenance, safety, and deployment

- Treat raw FDA input, product names, and API data as untrusted. Render text safely; do not reproduce the reference's HTML tooltip interpolation.
- Parameterized queries, allowlisted sorting, capped page sizes/query lengths, and bounded execution/concurrency. CORS allowlists are browser policy, not authentication or abuse prevention.
- Serve the public read-only dataset without secrets in browser code. Keep any ingestion/provider credentials only in local settings or CI secrets. No API accepts arbitrary SQL, shell commands, file paths, code, or downloads.
- Avoid logging full query strings, source payloads, or credentials. Log request IDs, status, duration, cache outcome, and dataset identity.
- Use pinned dependency versions, separate preparation/runtime dependencies, a reproducible container, and public health/readiness checks.
- Prepare from a pinned FDA source revision and snapshot hash, validate it, then publish database + metadata + saved overview as one versioned release. The container should already contain the validated database before startup.
- Acquire a newer snapshot manually/on demand in a separate workspace. The downloader currently refuses existing output directories and analysis validates fixed date bounds; extending coverage is a separate tested change, not an automatic refresh switch.
- Keep the previous release usable until the candidate passes data checks, CLI parity, resource budgets, and UI smoke tests. Roll back by releasing the previous image/compatible frontend, not mutating the live database.
- Preserve production/development separation and review before production updates. Project-site base paths and direct-link routing must be tested; hash-based demo routing is a simple Pages-compatible starting point.
- Leave the FDA repository's ignored local tests/review notes and current README unchanged during initial slices. Proposed Project Lab tests should be tracked for CI. Resolve upstream test-publication scope before relying on upstream tests in public CI.

Report terminology matters: these are reports mentioning products/reactions/outcomes, not unique people, causation, incidence, or relative risk. Multiple products and reactions do not identify a causal pair. Display this near the rankings and details, not only in a footer. [FDA interpretation guidance](https://open.fda.gov/apis/food/event/).

## 11. Incremental implementation and acceptance gates

### Slice 1: behavior contract and feasibility spike

Record assumptions for review: separate Project Lab repository; fixed current snapshot; raw search parity first; no writes/auth/live ingestion; approved cold-start UX. Establish representative oracle cases using the current Python functions without generating PNGs. Prototype preparation and one real filtered query before building a full dashboard or committing to a host.

Acceptance: source provenance is pinned; prepared output reconciles 97,652 unique reports; overall/year/product/empty selections agree with the CLI; database size, preparation time, peak memory, and warm query costs are measured. This is the first stop-and-review point.

### Slice 2: shared core and read-only database

Extract policy/validation without CLI regressions; prepare SQLite, metadata, and default overview. Keep raw product spellings tied to canonical terms. Check numeric normalization, reviewed aliases and non-alias neighbors, fractional/unit ages, zero and 125, missing gender/ages, duplicate IDs, invalid manifests, and product overlap.

Acceptance: existing CLI behavior is unchanged; deterministic snapshot/schema identities exist; preparation fails closed on incomplete data; independent query/oracle comparisons pass.

### Slice 3: backend MVP

Implement health/readiness, metadata, explore, and report pagination. Add response schemas, deterministic filters/sorting, cancellation-aware client behavior, bounded query/cache/concurrency settings, and contract tests. Start with one API worker and avoid long-running work directly in the asynchronous event loop.

Provisional performance targets, not current measured results: warm default/common queries p95 at or below two seconds under a small five-client test; process peak RSS below 350 MiB on the 512 MB target; typical overview JSON below 250 KiB uncompressed. Measure under constrained resources and recheck on the actual host; do not equate a local CPU quota with identical hosted performance.

Acceptance: counts and ranking order agree exactly; means agree within a defined tolerance; null serialization, invalid filters, query limits, concurrency, restart readiness, and unavailable data behave correctly. If budgets fail, optimize query plans/preaggregations or narrow the first release before adding visual features.

### Slice 4: React/D3 MVP

Implement year/product filters, five aggregate views, paginated reports, typed query state, snapshot labels, and a saved default overview. Test stale-response races, rapid filter changes, empty/no-age selections, keyboard/tap controls, back-button/reload state, and mobile overflow. No full-record parallel-coordinate view.

Acceptance: every view answers the same applied selection; saved/updating results cannot be mistaken for new results; chart labels and table equivalents expose essential values without hover; container resizing and unmounting leave no duplicate legends/tooltips/listeners.

### Slice 5: free deployment and portfolio integration

Confirm provider/account terms, provision the chosen free service only with user authorization, deploy a reviewed image and static frontend, and test an actual idle wake-up. Add the portfolio's Live Demo link only when the target works. Test HTTPS, CORS, direct links, API version compatibility, quota/error fallback, and rollback.

Acceptance: no paid services/add-ons; deployment reproduces the validated snapshot; initial saved overview is immediate; live backend queries recover after wake-up; the portfolio home does not load FDA data or wake the API merely to display a project card. Update relevant guides/READMEs at the completed milestone.

### Slice 6: expand intentionally

Add age/gender and canonical outcome/reaction filters with explicit AND-between-fields and OR-within-a-field policies. Specify whether facet counts reflect all active filters or deliberately exclude their own field; do not leave that choice accidental. For explicit age ranges, decide/document treatment of missing ages and inclusive boundaries.

Then add useful grouped comparison/parallel coordinates and a second project adapter. Verify memory, query cost, and failure isolation before combining multiple workloads. Extract shared components only where this second implementation demonstrates actual reuse.

## 12. Definition of a successful first release

An unfamiliar visitor can open the FDA demo from the portfolio, see what dataset they are exploring, change year/product filters, receive real backend-generated results, inspect matching reports, and share the same view. The existing CLI still works. The UI is truthful during sleeping/unavailable states. The project has reproducible data preparation, contract/regression tests, documented cost limits, and a clear path to another demo without rewriting the whole application.

Next action recommended: approve the repository boundaries and begin Slice 1 only. Do not start by deploying the existing CLI behind an HTTP endpoint or building a generic multi-project platform.
