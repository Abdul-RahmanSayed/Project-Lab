# FDA Explorer FastAPI Contract

**October 20 update:** The user approved the [smaller local backend slice](SLICE_3_SCOPE.md). That record supersedes this historical draft's reportKey transport, HMAC signing, SQL waiting queue, custom HTTP-handler cap, and filtered ETags. Implementation and measured results will be recorded separately; approval is not a claim that acceptance has passed.

Draft for review, October 15, 2026. **Documentation only: no API, frontend, dependency installation, service, or deployment is implemented by this document.** Read the [results review](RESULTS_REVIEW_2026-10-15.md) first. The review supports drafting this contract, not a production-readiness claim. Operational values below are proposals requiring approval and ASGI/resource tests before implementation acceptance.

## 1. Scope and Ownership

One read-only FDA release is active per API process. No authentication, user accounts, uploads, writes, ingestion, automatic refresh, arbitrary SQL, client-selected file paths, or runtime source downloads. Future projects get their own modules without copying FDA policy or allocating services now. Hosting remains $0; no provider eligibility or actual free limits were rechecked.

FDA owns canonical validation, raw suspect-product search, normalization/aliases, counting, age/gender rules, and its CLI. Project Lab owns the serving projection, HTTP schemas, release loading, admission/cancellation, and pagination. Neither HTTP code nor the browser reimplements normalization.

The old two-second target is superseded. The user's goal is **warm default all-year overview p95 < 10,000 ms with five simultaneous requesters**, within available free resources. There is no newly imposed hard latency target for every filtered selection. Sleeping-service wake-up remains separate, with an explicitly labeled saved overview.

## 2. Proposed Modules

This is a logical layout, not directories or code created in this task:

```text
backend/app/
  main.py                       app factory, middleware, router assembly
  core/config.py                trusted deployment settings
  core/lifecycle.py             startup validation and shutdown
  core/errors.py                public error translation, request IDs
  core/admission.py             bounded work ownership and deadlines
  projects/registry.py           explicit project capabilities
  projects/fda/router.py        HTTP only
  projects/fda/models.py        Pydantic request/response models
  projects/fda/service.py       release/selection routing and provenance
  projects/fda/repository.py    checked read-only SQL projections
backend/tests/                 contract, lifecycle, concurrency, parity tests
```

Use normal package imports and project-specific APIRouter composition, as described in [FastAPI's multi-file guide](https://fastapi.tiangolo.com/tutorial/bigger-applications/). Package the existing Project Lab serving logic once for both preparation and API use; do not copy query implementations or use machine-specific sys.path imports. Preparation dependencies and FDA raw pages stay outside the request-serving path.

During implementation, moving or modifying a pinned query/preparation/schema file requires a reviewed repin/rebuild and parity run. Moving files is not permission to alter policy.

## 3. Endpoints

All routes are read-only. GET is the MVP data method; CORS preflight is transport handling, not a data mutation.

| Route | Successful result | When unavailable |
| --- | --- | --- |
| /healthz | 200: {"status":"ok"}; process/event-loop liveness only | Transport failure if process not listening |
| /readyz | 200: {"status":"ready","releaseId":"..."} for the required FDA module | 503 DATA_UNAVAILABLE |
| /api/v1/projects | 200: registry with id, title, relative metadata URL, capabilities, ready, activeReleaseId or null | Registry still describes unavailable FDA; does not query reports |
| /api/v1/fda/metadata | 200 MetadataResponse | 503 DATA_UNAVAILABLE |
| /api/v1/fda/explore | 200 ExploreResponse for exactly one applied selection | Typed error; never an unrelated saved selection |
| /api/v1/fda/reports | 200 ReportsPageResponse, including a valid empty page | Typed error |
| /api/v1/fda/reports/{reportKey} | 200 ReportDetailResponse for a report in the applied selection | 404 REPORT_NOT_FOUND |
| /openapi.json and /docs | Generated API schema and interactive reference | No FDA query or ingestion is triggered by opening docs |

No generic execution endpoint or writable admin endpoint is added. Unsupported methods return 405, unsupported routes 404. Provider/proxy/network failures can occur before application JSON handling; clients must not assume every failure has a JSON body.

## 4. Release Selection and Readiness

Trusted deployment configuration selects a release directory and expected releaseId. Requests never select filesystem paths. Only one active release is served; historical-release hosting is not implied.

Startup loads a complete trusted offline bundle and checks artifact inventory/checksums, metadata/SQLite identity equality, supported schema/user_version, query-code pin, saved-default selection and label, and API-model compatibility. Open SQLite with mode=ro and query_only; never create indexes or rebuild/download data at startup. Hashes provide integrity within the trusted bundle, not a CI/supply-chain authenticity guarantee.

Before listening, initialization may be unreachable at the transport layer. Once listening, failed release validation leaves FDA unready: /healthz can be 200, /readyz and FDA data routes return 503. A missing/unreadable artifact, unsupported schema, mismatched query hash, malformed prepared response, or failed serving projection preflight must never yield ready=200. Today's access-denied release is a concrete required failure case.

Compute exhaustive report-key/response-size representability checks offline from the SQLite bundle, with evidence bound to its release and API representation version. Startup validates that evidence and its required projections; it does not rebuild reports or scan/render the entire raw snapshot. Adding checked API-compatibility evidence to the strict bundle inventory/metadata requires a reviewed preparation change and new release, not an untracked sidecar accepted on trust. Actual maxima were not measurable in this review.

Use [FastAPI lifespan initialization](https://fastapi.tiangolo.com/advanced/events/) rather than import-time loading. Publish the ready state only after validation completes. Do not rehash the database on every request or readiness probe. Normal SQL saturation alone is SERVICE_BUSY, not evidence of a corrupt release. Fatal serving failures mark the FDA module unready.

A release is immutable for the process lifetime. Switching it means a checked deployment/restart, not overwriting the live SQLite file. Rebuild the prepared payload and ETag for the selected release. Keep the previous deployment/release for rollback.

## 5. Shared Request Selection

metadata accepts only optional releaseId. explore accepts startYear, endYear, productFilter, and optional releaseId. reports accepts those plus limit, cursor, and sort. Report detail accepts the selection/release fields, not paging fields. Duplicate parameters and unknown parameters are rejected rather than silently ignored.

| Parameter | Meaning and proposed validation |
| --- | --- |
| startYear | Optional four-digit ASCII year; default coverage start; parsed integer, not float/bool |
| endYear | Optional four-digit ASCII year; default coverage end |
| productFilter | Absent means null/no product filter. Otherwise nonblank decoded text, max 256 Unicode code points and 1,024 UTF-8 bytes |
| releaseId | Optional fda-release-sha256: followed by 64 lowercase hex digits; defaults to active release |
| limit | reports only; integer 1-100, default 25 |
| cursor | reports only; absent on first page; opaque token, max 2,048 ASCII characters |
| sort | reports only; only reportId:asc is supported initially; default that value |

Named year bounds are inclusive and must satisfy coverageStartYear <= startYear <= endYear <= coverageEndYear. Reversed bounds are 422, not silently swapped. This does not change the CLI's handling of unordered year arguments.

Decode productFilter once using normal URL query decoding. Preserve its decoded nonblank value, including case and spaces, in appliedFilters. Match Python casefolded literal substrings against **raw SUSPECT names before normalization**, never SQL LIKE wildcards, canonical product aliases, fuzzy matching, or full-text tokenization. Percent, underscore, and plus signs remain literal search content; clients URL-encode them normally. Blank text is an error, not a shortcut to all reports.

Omission is the only HTTP spelling of no product filter; productFilter=null searches the literal text null. Multiple productFilter values are rejected, not combined as an undocumented OR selection.

Resolve defaults into an explicit AppliedFilters object with exactly startYear:int, endYear:int, productFilter:string|null. Product text is not rewritten to a canonical term. The initial frontend must pin releaseId after its metadata handshake; a valid but inactive ID gives 409 RELEASE_MISMATCH, never a silent fallback to a newer snapshot. An old cursor cannot select an old database.

The transport lengths above are new, visible API resource proposals, not changes to canonical FDA normalization. Confirm them with the serving release before acceptance. [FastAPI query models](https://fastapi.tiangolo.com/tutorial/query-param-models/) support declared constraints/forbidden extras; duplicate detection and exact HTTP-to-domain parsing still need explicit tests.

## 6. Response Models and Provenance

Future Pydantic models are the single executable schema source, with generated OpenAPI and generated TypeScript types. This Markdown is the design record, not a second hand-maintained OpenAPI YAML or independent client schema. Reject undeclared output fields. All nullable fields remain present. Use finite numeric types; no NaN/Infinity may escape. See [Pydantic finite-number types](https://docs.pydantic.dev/latest/api/types/#pydantic.types.FiniteFloat).

Snapshot data envelopes share these required fields:

| Field | Type / meaning |
| --- | --- |
| label | Explicit saved/queried data-snapshot label |
| isLive | Literal false; data are from the checked snapshot |
| source | Resource-specific enum: prepared-default, prepared-metadata, or sqlite |
| releaseId | Selected checked release identity |
| snapshotAcquiredAt | Original acquisition-completion instant as RFC 3339 UTC; not request time |
| Resource payload | overview, metadata, page, or detail, as specified below |

Each resource payload carries datasetId, policyVersion, appliedFilters where a report selection applies, and coverageNotes. These must agree with the envelope and active checked release. Do not expose absolute local paths, environment variables, secret material, or the raw internal metadata dictionary.

Request-specific metadata belongs in headers: X-Request-ID (server-generated), X-API-Contract: fda-v1, and X-FDA-Release-ID where available. Do not insert servedAt, requestId, or per-request timings into the immutable prepared body.

### ExploreResponse

Retain the existing runtime envelope and overview shape. source is prepared-default only for the exact resolved all-year/no-product selection; every other successful selection is sqlite. Its labels remain Saved overview / data snapshot and Queried overview / data snapshot.

| overview field | Required shape |
| --- | --- |
| datasetId, policyVersion | Version strings from the checked release |
| appliedFilters | Explicit resolved AppliedFilters |
| selectedCount, validAgeCount, missingAgeCount | Nonnegative integers; selected = valid + missing |
| ageMeans | Object: total, female, male; each finite number in 0..125 or null |
| yearCounts | Ascending [year,count] pairs for every applied year, including zero years |
| ageHistogram | Exactly 126 ascending [integerBin,count] pairs for bins 0..125 |
| genderCounts | Exactly ["Female",count], ["Male",count], ["Unknown",count], in that order |
| rankings | products/outcomes/reactions arrays of [canonicalTerm,count], at most 25 each |
| coverageNotes | Snapshot coverage and FDA interpretation caveats |

Histogram bins preserve the current floor-to-year presentation of valid fractional ages and exact 125. Mean calculations use full normalized ages, not bin centers. Invalid/missing ages remain in selected totals and gender/year counts, but not means/histograms. Gender-specific means are null if that gender has no valid ages. Mean parity tolerances remain absolute 1e-10 years / relative 1e-12.

Each canonical term is counted at most once per selected report. Rank ties use count descending then canonical term BINARY ascending, not browser locale sorting. Under a raw product filter, only matching raw suspect products contribute to product rankings; all retained reactions/outcomes of the selected reports remain eligible. Overlapping memberships must not be summed as unique reports.

Empty selection is 200, with zero selected/valid/missing counts, null means, empty rankings, and zero-filled years/histogram/genders. It is not 404 or a data-unavailable error.

Verified example from October 9: 2024-2026 and CARROTS selects 149 reports, 123 valid ages and 26 missing/invalid ages; yearCounts is [[2024,122],[2025,27],[2026,0]]. This is a projection example, not a complete response body.

**Prepared-byte validation:** FastAPI passes a directly returned Response through without automatic Pydantic conversion/validation. Therefore validate the prepared bytes against the declared public ExploreResponse at startup, keep its OpenAPI response declaration, and return the validated immutable bytes without per-request re-encoding. Validate SQL-produced responses before sending too. See [direct Response behavior](https://fastapi.tiangolo.com/advanced/response-directly/).

### MetadataResponse

source is prepared-metadata. metadata contains:

- datasetId, policyVersion, coreVersion, schemaVersion/schemaHash, queryHash, and a public source revision plus revisionKind; do not misrepresent a working-tree pin as a clean commit.
- reportCount, uniqueReportCount, pageCount, coverageStart/coverageEnd as calendar dates, acquisition-completion time, and explicit partial-year notes.
- defaultFilters, supported filter/sort declarations, proposed accepted input/page limits, and capabilities.
- termDisplayOverrides from the prepared dictionary only where display_label differs or disclosure is present. Product EXEMPTION 4 must retain its prepared disclosure label, not be presented as a known brand.
- Interpretation notes: report mentions are not unique people, causation, incidence, relative risk, or product-safety conclusions.

Keep Jan 1, 2026 in the final 2025 download-window description, while event-date filtering/counting assigns those reports to actual 2026. 2026 is a one-day partial year, not a complete year.

### ReportSummary and Detail

A reportKey is unpadded base64url of the exact UTF-8 report_id. It is an opaque URL-safe transport key, **not authorization**; reportId in JSON preserves the original FDA identifier. This avoids assuming original IDs are valid URL path segments. Reject noncanonical encoding or invalid UTF-8 with 400 INVALID_REPORT_KEY. Proposed representability bound: original ID <=512 UTF-8 bytes, reportKey <=684 characters. Validate the whole serving release against these bounds before accepting it; maximum ID lengths have not been verified in this review.

ReportSummary fields are reportKey, reportId, eventDate (YYYY-MM-DD), year, ageYears (finite 0..125|null), and gender (Female|Male|Unknown). No raw narratives or fabricated consumer fields are included.

ReportDetailResponse has source=sqlite and detail containing dataset/policy identity, appliedFilters/coverageNotes, and a report object with the summary fields plus:

- products in original ordinal order: ordinal (zero-based), rawName, original role, canonicalTerm|null, prepared displayLabel/disclosure|null, and matchesProductFilter. The last field is null with no product filter; otherwise true only for matching raw SUSPECT entries. Concomitant products are context, not a causal attribution.
- suspectProductsCanonical, reactionsCanonical, outcomesCanonical as distinct BINARY-sorted arrays. These describe retained report context, not necessarily the product-only filtered ranking.
- provenance.sourcePage as a validated manifest-relative reference and provenance.sourceIndex as one-based position. Never expose an absolute source path or use the supplied key to read arbitrary files.

The prepared schema does not retain raw reaction/outcome strings, original age/unit text, or complete raw reports. Do not reconstruct or fetch these at request time. Any such expansion requires a separate preparation/schema/policy review. Details outside the exact applied selection return 404 REPORT_NOT_FOUND, as do IDs absent from the release.

## 7. Deterministic Pagination

ReportsPageResponse has source=sqlite and page containing datasetId, policyVersion, appliedFilters, coverageNotes, sort, limit, returnedCount, items:ReportSummary[], hasMore:boolean, nextCursor:string|null. No total count is recomputed for each page; the matching explore response supplies selectedCount.

Use one initial order: **reportId ascending with SQLite BINARY collation**. It is an identifier order, not a promise of newest-first chronology. It fits the existing unique report_id index. New date/ranking sorts require a reviewed contract, query plan/index preparation, and new checked release if needed.

Select distinct report membership first, then page one row per report. Keyset boundary is report_id > lastReportId with the same BINARY collation and selection. Fetch at most limit+1; emit limit rows, use the extra row only for hasMore, and mint the cursor from the last emitted row. No OFFSET, unstable rowid-as-public-ID, or full selected_ids materialization in a public request.

Cursor proposal: base64url-encoded JSON plus HMAC-SHA256 authentication using a server-only deployment key of at least 32 random bytes. The payload binds cursor version, API contract, releaseId, exact selection digest, sort, limit, and lastReportKey. Selection digest is SHA-256 of sorted-key, whitespace-free canonical JSON of resolved AppliedFilters, retaining exact decoded product text. Changing case/spaces can therefore invalidate a cursor even if the selected IDs happen to match.

For this digest, use the existing content-hash convention: sort_keys=true, ensure_ascii=true, separators comma/colon without whitespace, allow_nan=false, then UTF-8. Cursor encoding is unpadded base64url(payload bytes), a dot, and unpadded base64url(HMAC-SHA256 of those same payload bytes); compare signatures in constant time. Reject duplicate/unknown JSON keys and unsupported cursor versions. Tokens are opaque to clients; no browser implementation of this digest/signing protocol is required.

Verify token size, signature, types and canonical encodings before use; do not allow SQL or file paths in token fields. A client must resubmit the same filters/sort/limit. Tampering/malformed tokens give 400 INVALID_CURSOR; valid tokens with different selection/sort/limit give 409 CURSOR_CONTEXT_MISMATCH; inactive release gives 409 RELEASE_MISMATCH. Derive lastReportId only after verification and decoding, then bind it as a SQL parameter.

Cursor lifetime is bound to release/contract/signing key, not an in-memory session or new database write. Restart with the same key and release preserves valid cursors. Rotation invalidates old signatures; the client restarts from page one. No wall-clock expiry is introduced initially. The key is neither a browser credential nor API authentication and must never be derived from a public release hash or committed. Missing required signing configuration is a startup configuration error, not a constant-key fallback.

Last/empty page is 200 with hasMore=false, nextCursor=null. Empty selection returns no items. Cursor boundaries must not create duplicates, missing reports, or mismatched summary/detail selection.

## 8. Capacity, Deadlines, and Cancellation

Initial proposals, **not measured optimums or new user SLAs**:

| Setting | Proposed initial value |
| --- | ---: |
| ASGI worker processes | 1 |
| Accepted HTTP handler tasks | At most 32; no additional unbounded application HTTP wait queue |
| Active SQLite jobs | At most 5, matching the profiled concurrency |
| Pending SQLite jobs | At most 5; admitted work therefore <=10 |
| SQL-backed request budget | 30 seconds total, including queue wait and response construction |
| Product input | 256 code points / 1,024 UTF-8 bytes |
| Report page | Default 25, maximum 100 |
| Encoded page/detail response | Maximum 1 MiB; validate release representability first |
| Arbitrary filtered response cache | Disabled |
| Prepared overview | One immutable entry, rebuilt for the checked release and public schema |

The default, metadata, registry, and health paths must not wait for a SQL slot. Keep their processing small and do not call blocking SQL from the async event loop. Use an explicitly bounded executor/admission owner for explore filters, report pages, and details. Do not assume the framework's shared thread pool provides this policy; see [Starlette thread-pool behavior](https://www.starlette.dev/threadpool/).

SQL admission alone does not bound HTTP sockets or handler tasks. The proposed 32-handler application cap rejects overflow promptly with SERVICE_BUSY rather than allocating another wait queue. Configure finite server connection/backlog/header bounds during implementation and test them separately; external ingress is not controlled by this prototype. At most ten SQL-backed requests can occupy handlers, leaving headroom for the default/health paths during ordinary SQL saturation, not a guarantee against arbitrary traffic floods.

Admit before executor submission: active jobs use the five slots, pending jobs occupy only five bounded queue entries, and overflow receives 503 SERVICE_BUSY with Retry-After: 2. Do not submit an unbounded number of futures and then gate them with a semaphore.

Create, use, and close each SQLite connection in its owning worker. Configure a bounded lock wait and cooperative progress/deadline checks during implementation; the current runtime does not supply these hooks. Required connection/preparation changes must preserve the existing read-only and policy invariants and trigger repinning if pinned files change.

Start the deadline when the request is received, not when a worker becomes free. Carry the remaining budget through queued work, SQL, model validation and encoding. Deadline exhaustion returns 503 QUERY_TIMEOUT, not zero reports. A 30-second resource deadline does not claim that every filter meets ten seconds.

On disconnect or supersession, cancel pending work before dispatch. For executing work, signal a cancellation event checked by the SQLite progress handler; a carefully synchronized interrupt may also be used. Python documents [query progress cancellation and cross-thread interrupt](https://docs.python.org/3.14/library/sqlite3.html#sqlite3.Connection.set_progress_handler); Starlette provides [disconnect detection](https://www.starlette.dev/requests/). Canceling an await/future alone is not proof that the native SQL stopped.

A disconnected client may receive no HTTP response; record cancellation internally rather than inventing a public 499 response. Deadline responses are attempted only while connected, and canceled/timed-out work cannot populate a result cache.

**The SQL slot stays owned until its worker has stopped and closed the connection**, even if the HTTP waiter has timed out or disconnected. Do not admit replacement work early and accumulate hidden workers. Cancellation of noncooperative I/O is best effort, not an instantaneous thread-kill guarantee. Test stalled workers and shutdown explicitly; sustained fatal worker failures make FDA unready, without unbounded replacement threads.

Resource failure/oversized responses must not silently truncate terms, discard reports, or alter search policies. Reject with a typed error and revise reviewed limits/preparation if the serving release cannot fit them.

## 9. Errors and Headers

All application errors use this shape; details contain safe field names/reason codes, not submitted values, raw cursors, paths, SQL or stack traces:

```json
{
  "error": {
    "code": "INVALID_FILTER",
    "message": "startYear must not exceed endYear.",
    "details": [{"field": "startYear", "reason": "reversed_range"}],
    "retryable": false
  },
  "requestId": "00000000-0000-4000-8000-000000000001"
}
```

The example request ID is illustrative. Its actual value must equal the response X-Request-ID.

| HTTP status | Code | Meaning |
| --- | --- | --- |
| 400 | INVALID_CURSOR / INVALID_REPORT_KEY | Malformed encoding, payload or cursor signature |
| 404 | REPORT_NOT_FOUND / NOT_FOUND | Missing/out-of-selection report, or unknown route |
| 405 | METHOD_NOT_ALLOWED | Unsupported method |
| 409 | RELEASE_MISMATCH / CURSOR_CONTEXT_MISMATCH | Version/selection context changed; restart/reconcile, do not silently substitute |
| 414 | REQUEST_TARGET_TOO_LONG | Proposed application target limit: 8 KiB; upstream servers may reject earlier |
| 422 | INVALID_FILTER / INVALID_PARAMETER | Invalid bounds/types, blank/long product, unknown/duplicate arguments, unsupported sorting/limit |
| 503 | DATA_UNAVAILABLE | Checked release unavailable/incompatible or module unready |
| 503 | SERVICE_BUSY | Bounded admission full; retryable, Retry-After: 2 |
| 503 | QUERY_TIMEOUT | Total SQL-backed request budget exhausted; no automatic repeated expensive retry |
| 503 | RESPONSE_TOO_LARGE | Result cannot be represented inside the reviewed byte limit; never silently clipped |
| 500 | INTERNAL_ERROR | Generic unexpected failure; server-side diagnostic reference only |

Global server saturation is 503, not a fabricated per-user 429 policy. No per-user rate limiter is claimed. All errors and health/registry/readiness responses use Cache-Control: no-store. Response headers remain small; X-Request-ID and allowed CORS headers also apply to error paths.

## 10. Release-Bound Caching and Conditional Requests

Initially retain only the prepared default. Its identity includes API representation contract, releaseId, datasetId, policyVersion, schema/query identity, and exact resolved default filters. A changed release or public shape must replace/revalidate the payload; no cache entry survives under a mismatched identity.

Prepare/validate its bytes once at startup. ETag is a quoted digest of the actual response bytes; request-specific headers do not enter it. Default API responses use Cache-Control: public, max-age=0, must-revalidate. Validate syntax, release, exact selection and readiness before an If-None-Match hit can return 304. Errors must not become 304, and custom filters must never use the prepared-default ETag. Conditional requests follow [HTTP precondition semantics](https://www.rfc-editor.org/rfc/rfc9110.html#name-if-none-match).

Other data endpoints initially use no-store and compute their representation ETag only after normal admission, selection, model validation and encoding. A conditional hit can return 304 for that exact representation, but saves no SQL work and creates no server response cache. There is no filtered cache, stale-while-revalidate, error cache, or coalescer. If later needed, propose finite entry/byte limits, release/representation/filter/page keys, eviction and cancellation ownership, then measure hit/miss/mixed uncached paths including queue wait. Do not silently relax semantics to manufacture a cache hit.

Static frontend fallback is a separate release-bound asset. It may display immediately with its actual filters and saved label while the API wakes. If the backend has another release, return/version-reconcile explicitly; never combine old overview numbers with new pages. Custom filters cannot reuse the default fallback as their answer. No periodic wake-up traffic is permitted.

## 11. Public Safety and Observability

Keep browser CORS to configured frontend/local-development origins, credentials disabled, no wildcard credentials; expose ETag, X-Request-ID, X-API-Contract, X-FDA-Release-ID and Retry-After as needed. Origin is scheme/host/port, not a repository URL path. CORS is not authentication or an abuse-control system; see [FastAPI CORS guidance](https://fastapi.tiangolo.com/tutorial/cors/).

Only parameterized values and fixed/allowlisted sort clauses enter SQL. Keep raw strings as data; no HTML interpolation, arbitrary code, filesystem paths, download URLs or writable runtime databases.

Log route templates, request IDs, status, release identity, response mode, queue/service/total durations, admission/cancellation outcome and bounded-cache state. Disable or redact default access logs that include query strings. Do not log raw searches, report payloads, cursors, keys, environment values, or absolute paths. Debug traceback exposure is disabled.

No silent retries of timed-out expensive queries. A future client uses one shared bounded readiness/wake-up flow, not a polling loop per chart. Rendering and network time are client measurements and must not be passed off as server-only latency.

FDA report mentions are not unique people, causation, incidence, relative risk, or product-safety conclusions. Keep this interpretation near relevant data, including details and overlapping product/reaction memberships.

## 12. Acceptance Before API Implementation Is Declared Complete

| Check | Required evidence |
| --- | --- |
| Restore input access | Readable chosen release; full inventory/hash/schema/query pin checks and fresh parity |
| Input validation | Unknown/duplicate fields, malformed UTF-8/cursors/keys, literal %, _, +, Unicode casefolding, invalid ranges and transport bounds |
| Public schema | Required/null fields, finite numbers, full zero padding, prepared bytes validated against declared OpenAPI model |
| Selection parity | Existing nine oracle cases plus randomized/representative filters; no default shortcut for changed filters |
| Pagination | Concatenating all pages equals exact oracle IDs; stable tie/order rules, no overlap/gaps, zero/last pages, changed context/release/key and restart cases |
| Detail fields | Only prepared allowlist, raw-versus-canonical distinctions, source positions, out-of-selection 404, EXEMPTION 4 labeling |
| Capacity/queue | <=32 HTTP handlers, <=5 active and <=5 pending SQL jobs; bounded server ingress; overload rejection; health/default stay responsive under SQL saturation; wait included in timings |
| Deadline/cancel | Queue expiry, running SQL interrupt/progress, disconnect, no hidden continuing workers or early permit release |
| Lifecycle | Cold startup, unreadable/corrupt inputs, wrong schema/query/response, full process restart and release replacement/rollback |
| Cache isolation | One prepared entry, changed release/schema/filters cannot hit; correct ETag/304/error behavior |
| Performance/resources | Real ASGI five-client default p95 <10 s under constraints; repeated and mixed SQL, overload and cancellations; full API memory/image/disk accounting |
| Hosting/CI | Separate reviewed package/source pins and container/CI reproducibility; verify actual free limits before any separately authorized provisioning |
| Type generation | OpenAPI-derived client types cover tuple pairs, enums, nullable means, errors and pagination; no conflicting handwritten machine spec |

Do not infer HTTP readiness from the 2.08 ms encoded-byte benchmark. Do not change the old CLI to appease stale upstream tests as a side effect. Choose/pin framework/runtime versions during the separately authorized implementation phase, with compatibility and dependency tests.

## 13. Decisions Requiring Review

This draft proposes, rather than claims user approval for: reportId ascending as the only initial sort; URL-safe reportKey transport; HMAC cursor configuration; 25/100 page sizing; product/token/response bounds; 32 HTTP handlers, five active plus five pending SQL jobs; and a total 30-second SQL-backed request budget.

The present release-access problem and serving-field/size preflight must be resolved before acceptance testing. Approve or revise these design choices, then authorize a bounded backend implementation slice. The frontend and all deployment/account/repository/commit/push work remain outside this contract task.
