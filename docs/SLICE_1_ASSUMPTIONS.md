# Slice 1 Assumptions and Behavior Contract

Date: October 9, 2026. Baseline: [FDA_DASHBOARD_PLAN.md](FDA_DASHBOARD_PLAN.md), copied byte-for-byte from the supplied plan.

- Project Lab owns this local feasibility prototype. It was an ordinary folder with no Git repository at the start. No repository or branches are created in this slice.
- Use the existing completed snapshot, covering January 1, 2002 through January 1, 2026. Revalidate every manifest-listed report; pin the FDA Git revision, actual source hashes, manifest hash, and page hashes.
- The current `part2.py` functions are the oracle. Load them only through an explicit local `--source-repo` preparation/verification argument. This temporary adapter is not the eventual packaged dependency or API import design.
- Do not change the FDA checkout or portfolio. Do not download new FDA data or generate oracle PNGs.
- Preserve raw casefold substring search on products whose role is exactly `SUSPECT`. Apply inclusive year bounds. Product search precedes canonical normalization; only matching raw suspects contribute to filtered product rankings.
- Reuse the current normalization, narrow aliases, age conversion, gender handling, and disclosure label functions. Deduplicate canonical terms within each report. Retain all outcomes/reactions of selected reports. Keep reports without valid ages in totals, and exclude them only from age calculations.
- Histogram bins are one year wide from 0 through 125, including fractional ages and exact age 125. Missing averages are JSON null. Annual counts include zero-count years. Unknown gender remains counted.
- Require exact selected report IDs, all term counts, ranking order, annual counts, histograms, and age/gender counts. Compare means with absolute tolerance `1e-10` years or relative tolerance `1e-12` to accommodate floating-point summation order.
- Keep generated databases, machine-readable oracles, caches, and measurements under ignored `generated/`. Keep the local Python environment ignored. Preserve reviewable source and a small results document outside generated output.
- Measure offline preparation, oracle, and lightweight query memory separately in fresh processes. Warm latency covers one sequential read-only connection, no result cache, and the complete overview plus JSON serialization. These are local measurements, not host guarantees.
- React/TypeScript/D3, modular FastAPI, a prepared read-only SQLite database, $0 hosting, sleeping services, and a labeled saved overview remain the intended architecture. No frontend, service, account, deployment, repository publication, commit, or push is part of Slice 1.

## Prototype Boundaries

The SQLite query prototype uses parameterized `instr` against Python-casefolded raw names and a read-only URI connection with `mode=ro`. See the official [SQLite scalar functions](https://www.sqlite.org/lang_corefunc.html) and [URI reference](https://www.sqlite.org/uri.html). Each ranking aggregates distinct report/term memberships independently, avoiding multiplication across products, outcomes, and reactions.

The `reports(year)` index supports inclusive year selection. Product membership primary keys support per-report lookup; arbitrary literal substrings still scan candidate raw product names. Record query plans before adding more indexes. No full-text search substitutes for the existing substring policy.

This prototype is not a stable public database schema or API contract. Packaging the shared analysis core, deployment dependency locking, saved overview publication, concurrency limits, and API readiness checks remain later slices.
