# Approved Local Frontend Slice

Authorized October 20, 2026 after the local backend checkpoint was committed. This is Slice 4 only, consuming the existing read-only API contract. No deployment, account creation, provider provisioning, publication, commit, push, FDA-source or portfolio modification is authorized.

## Implementation Design

- Separate `web/` React/TypeScript/Vite app. D3 owns scales/geometry; React owns all SVG/DOM, controls and request state. Existing Project Lab contracts and explicit D3 scope take precedence over generic dashboard SDK scaffolding. No plugin framework, chart editor, result cache, signing secret or job queue.
- Five evidence views: actual-year report counts, the existing 126 age bins, and product/outcome/reaction rankings. Up to five chart instances, hundreds rather than tens of thousands of marks. Exact-value accessible tables accompany all views. No map, 3D, new aggregation/normalization, parallel coordinates or additional filters.
- One committed year/raw-product selection, separate draft controls and Apply. Hash-backed URLs retain release, committed filters, tab, page size and fixed report-ID sort. Back/forward and invalid-link repair are explicit. No persistent personal defaults or browser data cache.
- Abort superseded fetches and reject late responses by generation, release, dataset/policy and exact filter identity. Preserve previous data only under its original displayed-selection label. Never label a saved default as a changed selection.
- An offline export validates the selected release through the existing API lifecycle, then exports public metadata, exact saved default and generated OpenAPI/TypeScript contracts. No database, raw pages, local source paths or runtime preparation in the browser. Saved artifacts are release-bound and checked at build time.
- At most three bounded metadata connection attempts, then manual retry. SQL requests do not automatically retry. Distinct starting/querying, API unavailable/busy/limit, invalid, empty and snapshot-mismatch states. No polling, wake-up pings or hosted availability claim.
- Paginated report summaries and on-demand retained details. Cursor history stores only a bounded set of bookmarks, not result pages. Native modal details preserve focus, support Escape and retain source provenance. Raw labels render as text, never HTML.
- Quiet operational styling. The October 20 follow-up matches the production portfolio's default dark background, violet controls, mint accents and Inter/JetBrains Mono typography, with stronger text/control contrast where needed. Distinct distribution/ranking and alert colors remain. No decorative media, marketing hero or floating section cards. Charts are the evidence-bearing visual assets.
- Desktop shows coordinated plots; mobile stacks plots, collapses controls and preserves active-selection labels. Stable chart dimensions, container-driven scales, wrapping labels, keyboard/tap equivalents and reduced-motion support. No hover-only essential values.

## Verification Boundary

Typecheck/build; unit checks for URL/selection/response identity; real-browser HTTP workflows against the checked backend; mocked network boundaries for stale responses, offline/busy/invalid/version changes and empty/no-age cases; desktop/mobile screenshots and overflow/mark checks. Preserve backend source/release bytes and recorded Slice 3 semantics. Browser timing is local and does not establish actual hosted CPU/memory, internet latency, sleeping-service recovery or $0 provider eligibility.

Review the completed local frontend results before Slice 5. Completion/teaching/resume/Flex reminders remain pending until the agreed feature is genuinely complete and verified end to end. FDA reports are not unique people, causation, incidence, relative risk or product-safety conclusions.
