# Local FDA API Contract

Implemented for the smaller slice approved October 20, 2026. The [approved scope](SLICE_3_SCOPE.md) supersedes the more elaborate [October 15 draft](FASTAPI_CONTRACT.md). Executable response schemas live in [models.py](../backend/fda/models.py); the running server generates `/openapi.json` and `/docs`. No separate handwritten machine schema is maintained.

## Local Boundaries

One process serves one checked, read-only release. Startup verifies the artifact inventory, checksums, SQLite/metadata/schema identity, query-code pin, prepared-default selection and public schema. Unreadable or inconsistent inputs leave the process alive but FDA unready. Startup never downloads raw data or rebuilds the database. The exhaustive retained-field/size check is an offline acceptance step, not a new trusted sidecar or a raw-data scan on every startup.

The existing `data-build` serving modules are packaged once with the API, unchanged. Normal installed Python imports work outside the checkout. The FDA CLI, source/policy pins and raw pages remain separate. Changes to pinned preparation/query/schema files still require a reviewed repin/rebuild; none was needed for this slice's new report projections.

## Requests

| Route | Purpose |
| --- | --- |
| `GET /healthz` | Process liveness, independent of release readiness |
| `GET /readyz` | Checked FDA readiness and selected release ID |
| `GET /api/v1/projects` | One static FDA capability entry; no generic plugin framework |
| `GET /api/v1/fda/metadata` | Public coverage, provenance, supported filters and limits |
| `GET /api/v1/fda/explore` | Overview for the exact applied selection |
| `GET /api/v1/fda/reports` | Deterministic next-page report summaries |
| `GET /api/v1/fda/reports/detail?reportId=...` | Retained fields of one matching report |

Selection fields are optional `startYear`, `endYear`, `productFilter`, and `releaseId`. Omitted years mean snapshot bounds; bounds are inclusive. Omitted product means no product selection. Nonblank product text is preserved, not trimmed, alias-rewritten or tokenized. Matching remains Python-casefolded literal substring search over raw SUSPECT names. Literal `%`, `_` and `+` are supported when URL-encoded normally. The word `null` is a literal search, not no filter.

Reject unknown/repeated fields, reversed/out-of-coverage years, blank or oversized product text, and unsupported sorting/page sizes. Product limits are 256 characters and 1,024 UTF-8 bytes; URL limit is 8,192 bytes. Report IDs are ordinary query strings, at most 512 UTF-8 bytes. Client inputs never select files, SQL text, table names or arbitrary code.

Requests may pin the active `releaseId`; an inactive valid ID returns `409 RELEASE_MISMATCH`. No silent substitution of another release or default selection is permitted. January 1, 2026 remains actual 2026 event data, explicitly a partial year, despite its placement in the final 2025 acquisition window.

## Responses

All data envelopes contain `label`, `isLive:false`, `source`, `releaseId`, and original `snapshotAcquiredAt`. Selected payloads contain dataset/policy identity, explicit applied filters and coverage/interpretation notes. Request IDs and API/release identity headers are separate from reusable prepared bytes.

- Overview preserves all existing counts, nullable finite age means, zero-filled years, 126 age bins, fixed gender order, and top-25 rankings. Each term counts once per selected report, with count-descending/BINARY-term tie order. Raw product filtering affects product ranking membership before normalization. Empty selection is successful zero counts/null means, not an error.
- Metadata exposes an allowlist, not local filesystem paths or the internal metadata dictionary. A working-tree source pin is labeled honestly. EXEMPTION 4 keeps its prepared display/disclosure label.
- Summary contains original report ID, event date/year, normalized age or null, and gender. There is no encoded `reportKey`.
- Detail adds raw product names/roles/ordinal positions, canonical/display/disclosure fields, product-match flags, distinct canonical suspect/reaction/outcome terms, and manifest-relative source position. Original raw age/unit/reaction strings and full raw JSON are not retained and are not fabricated. Out-of-selection or missing reports return 404.

The actual schemas and nullable/tuple representations are available in generated OpenAPI. TypeScript generation belongs to the later frontend slice. Pydantic validates the prepared bytes at startup and newly queried output before encoding. Output over 1 MiB is rejected, never clipped.

## Report Pages

Default size 25, maximum 100. Initial order is `reportId:asc`, SQLite BINARY identifier order, not newest-first. Use the existing unique-ID index and a last-ID boundary, fetch one extra row for `hasMore`, and avoid OFFSET/full selected-ID loading in public requests.

An unsigned base64url JSON bookmark records token version, release, exact filter digest, sort, page size and last original report ID. Maximum 2,048 characters. Strict parsing and context checks still apply; there is no signing secret, session store or authentication claim. Editing a bookmark may skip public matching rows but cannot bypass current filters or parameterized SQL. Changed selection/page settings require restarting pagination; same-release restarts preserve bookmarks. Empty/last pages return `hasMore:false` and `nextCursor:null`.

## Resource Handling

- One Uvicorn worker; built-in connection/task admission limit 64 and backlog 64, not a second custom application HTTP queue. This is not a firewall, a strict TCP accept limit or a guarantee against traffic floods. Server-level rejection can be plain-text 503 rather than application JSON.
- Five admitted SQL jobs, no application waiting queue. Admission happens before executor submission. Excess work returns `503 SERVICE_BUSY` with `Retry-After: 2`. This is a work limit, not a five-user limit.
- Prepared default, metadata, health and registry do not take SQL slots. They remain available during ordinary SQL saturation; global ingress overload can still reject requests.
- The 30-second SQL-backed budget starts on request receipt and includes dispatch, query, validation and encoding. Timeouts return `503 QUERY_TIMEOUT`, not zero reports. This is a resource cutoff, not a new latency target for every search.
- Disconnect/deadline signals reach SQLite through a cooperative progress callback. A slot remains occupied until its worker closes the connection and finishes. No replacement thread is admitted early. Noncooperative I/O is not instantaneously killable; shutdown waits for active workers and a stuck process may need an external restart.
- Only the exact all-year/no-product selection gets prepared overview bytes. Its ETag is computed from those bytes. A valid matching GET may return 304 only after checking readiness/release/selection. Other data uses `no-store`, without filtered ETags or a general cache.

## Errors and Logs

Application errors contain a safe code/message, empty safe details, retryability and request ID. Invalid parameters are 422; malformed bookmarks 400; missing routes/reports 404; unsupported methods 405; changed version/context 409; oversized URLs 414; unavailable/busy/timed-out/oversized results 503; unexpected failures 500. No submitted values, cursors, SQL or paths are echoed. A disconnected caller receives no fabricated 499 response.

Server access logs containing query strings are disabled. Optional application logs use route templates, request IDs, status, release identity, outcome and elapsed time, not raw searches/report payloads. CORS allows only configured origins, without credentials; it is not authentication. Loopback binding is the local runner's default and only supported binding in this slice.

## Acceptance Boundary

See [Slice 3 results](SLICE_3_RESULTS.md) for actual checks and limitations. Local HTTP is not internet/host/browser verification. Free-provider eligibility, actual hosted limits, container/CI reproducibility, frontend behavior, and deployment remain separate reviewed work. No accounts, publication, commits or pushes are included. FDA reports do not establish unique people, causation, incidence, relative risk or product-safety conclusions.
