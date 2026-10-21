# Approved Smaller Local Backend Slice

Approved October 20, 2026. This supersedes the corresponding proposals in the October 15 FastAPI draft; untouched data and interpretation policies remain in force.

- One local FastAPI process, with FDA routes/models/queries separated from shared startup and job ownership. Package and reuse the existing query implementation, without copying it or adding machine-specific import paths.
- Restore a readable checked input, or regenerate the same pinned snapshot without modifying the inaccessible historical release. Do not broaden OneDrive permissions or take ownership of unrelated folders.
- Health/readiness, metadata, overview, report pages and report details. Report IDs use ordinary URL-encoded query fields, not a separate reportKey format.
- Report ID ascending, SQLite BINARY order. Pages default to 25, maximum 100. Unsigned, bounded next-page bookmarks check release/filter/order/page-size context; they are not authorization. Editing a bookmark can skip public matching records, never bypass the current selection or SQL parameterization.
- Five active SQL jobs, no application pending queue. Excess SQL work receives a clear busy response. The prepared default, metadata and health do not use SQL job slots. Use the server's finite connection/task limit, not a second custom HTTP admission subsystem.
- A 30-second total SQL-backed resource budget, including dispatch and response construction. Cancel real SQLite work on disconnect/deadline; do not release its slot until the worker actually finishes. This is not a ten-second target for every filter.
- One release-bound prepared default, no general result cache and no filtered-response conditional-request machinery. No signing key, accounts or sessions.
- Check actual serving fields and size bounds offline before acceptance. Reject oversized input/output clearly; never truncate searches or data. Runtime validation remains fail-closed.
- Preserve raw suspect-product substring matching, Unicode casefolding, normalization/aliases, counting, age/gender rules, and the existing FDA CLI. Preserve January 1, 2026 as actual 2026 event dates despite its download-window placement.
- Test real local HTTP, correctness against the original Python analysis, pagination, errors, overload, cancellation, startup failures and resource use. Warm default p95 must remain strictly below ten seconds with five simultaneous readers. Measure repeated/mixed uncached work and disclose busy responses separately from successful latency.

Frontend, deployment, provider/account setup, repository publication, commits and pushes are not authorized. The original baseline plan is unchanged. Reproducibility is local-runtime/working-tree evidence, not a CI/container or hosted guarantee. FDA report mentions do not establish unique people, causation, incidence, relative risk or product safety.
