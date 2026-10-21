# Slice 5B: Local Deployment Preparation Results

**October 21 follow-up:** Docker/WSL2 are now available. The unchanged image built,
and constrained Linux correctness/HTTP/resource checks passed. See the separate
[Linux results](SLICE_5_LINUX_RESULTS.md); the unavailable-container findings below
describe the earlier preparation checkpoint. Public-runtime security review and
hosted acceptance remain pending.

Prepared locally across October 20-21, 2026, after Abdul explicitly approved local
packaging, container/API-origin wiring and local testing. **The verified Windows
preparation and HTTPS paths pass; Linux/container and hosted acceptance remain
pending. This is not completion of Slice 5 or the end-to-end feature.** No account,
provisioning, publication, repository visibility change, portfolio edit, commit or
push occurred. [Scope/proposal](SLICE_5_DEPLOYMENT_PROPOSAL.md), [reproduction guide](../deployment/README.md).

## Delivered Locally

- A deterministic, five-file release archive and reviewed archive/file checksum lock.
  Packaging/extraction reuses the existing release and query-code validation. Exact
  member names/order/sizes/hashes, fixed timestamps/owners, ordinary files only,
  bounded download/extraction, and no overwrite of existing output directories.
- A build-only downloader restricted to a fixed-tag asset in the reviewed GitHub
  repository. It is not called by startup or HTTP requests. Its network path was
  tested with a local stream fixture, not a nonexistent published release.
- Fresh inherited extraction-directory permissions and read-only installed files,
  without copying a private temporary-directory ACL. This does not repair or repin
  the old Windows builder. The database remains read-only at the SQLite connection.
- Candidate Dockerfile with explicit context allowlisting, pinned Linux/amd64 base,
  installed runtime package, baked-in snapshot, non-root serving user and no second
  compressed-archive copy in the final stage. No container build/run is claimed.
- Deployment entry point using the existing API factory and pinned bytes, exact
  HTTPS CORS settings, one worker, five SQL jobs, no pending queue and unchanged
  30-second SQL budget. The local loopback runner and analysis/query modules remain
  unchanged. Test-only loopback TLS options introduce no public control endpoint.
- Trusted build-time HTTPS API origin and credential-free requests. Dedicated
  deployment builds require the origin; normal builds retain the local proxy.
  Production-style output is separate from the normal preview and works under
  `/Project-Lab/` with hash URLs. No secrets, runtime API-URL selection, extra cache,
  polling/keep-awake or data-policy changes were added.

## Artifact Identity

- Same selected release: `fda-release-sha256:18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194`.
- Database: **62,152,704 bytes**, SHA-256
  `bdfd771ede151a2784a83ff1e9ba1faad727491cce2bddf73a0499521b4d475f`.
- Archive: **17,855,778 bytes / 17.86 MB / 17.03 MiB**, SHA-256
  `3895e5b06e9ea5e7432ed7e0a8c58efe85024b2fda32ac5f235d25319d7e6ba1`.
  The five uncompressed files total **62,354,679 bytes**. Independent local repacks
  matched the reviewed archive; this is not cross-runtime compression reproducibility.
- Final locally tested API wheel: **44,611 bytes**, SHA-256
  `12ee75c9c69961ef69ebb0e196d3584171852dff794605720166875d996e0878`.
  Query/runtime/API/deployment source bytes were compared with wheel members; the
  four HTTPS checks ran its isolated installed copy, with the existing pinned dependencies.
- Candidate base: `python:3.14.2-slim-bookworm`, Linux/amd64 digest
  `sha256:34bb71a7de6dbecc839d8d6f8aaff8c4bf67ce01634764eaf929cb64d3ae315e`.
  Actual registry metadata was read, not an invented digest. All 14 pinned runtime
  dependencies plus setuptools 80.9.0 downloaded as compatible Linux/universal wheels.
  Download availability is not installation/execution, security or container acceptance.

No saved frontend data, database schema, query code, normalization, age or counting
policy changed. The small deployment lock is a source-controlled candidate, not
the archive/database. Ignore checks confirmed archive, database, wheel and TLS key
exclusion. The API's new package still has the local 0.1.0 package version; its new
bytes are identified by the wheel hash, not presented as the earlier Slice 3 wheel.

## Verification Results

| Verification | Final result | Boundary |
| --- | --- | --- |
| Preparation/configuration suite | **12 passed** | Deterministic repack, extraction/read-only round trip, default/filtered counts, tampering/wrong release, missing/extra/duplicate/path/link/size failures, strict pins/settings, URL/redirect/download bounds, CORS/readiness. |
| Existing API suite on unpacked release | **12 passed** | Paging/details, literal text, null/empty behavior, version/shape/readiness failures, admission, timeout/disconnect and retained slots, CORS/size checks and unchanged DB. |
| Frontend unit suite | **20 passed** | Previous 17 checks plus three API-origin checks; raw transport and explicit credential omission verified. |
| Build/typecheck | **Pass** | Normal and dedicated deployment builds; missing deployment origin deliberately failed before output. |
| Existing browser regressions | **22 passed** | Normal proxy preview, default/filtered table parity, keyboard/touch, desktop/mobile layouts, races, errors and saved labels. |
| Separate-origin HTTPS suite | **4 passed** | Installed API wheel, actual loopback TLS/CORS, project-path assets/hash state, wrong release, real stopped process and Retry recovery. |

The initial preparation run's assertions passed but cleanup failed because a test
used SQLite's transaction context manager without closing its connection. The test
now explicitly closes that handle. Two existing API corruption tests initially
could not overwrite read-only copies; only those temporary fault-injection copies
were made writable, not the serving release. All affected checks passed afterward.
The previously recorded Starlette/httpx deprecation warning remains; dependencies
were not upgraded to hide it. An initial sandbox pip build failed on sandbox temp
permissions; the approved no-network host build succeeded. These failures were not
data-policy failures or silently excluded cases.

### Actual Local HTTPS Findings

The static build was served at `https://127.0.0.1:4174/Project-Lab/`, without Vite's
proxy, and called the separately bound API at `https://127.0.0.1:8767`.

- Default **97,652 reports** and five charts loaded. 2024-2026 CARROTS returned
  **149**; report pages/details loaded; literal `+` returned **1,811** and survived reload.
- Correct browser origin received the required CORS headers, including on a real
  wrong-release **409**. A `localhost` page with a different origin could not read
  the API and retained the labeled saved view with Apply disabled. A nonbrowser
  request still received HTTP 200 without an allow-origin header: CORS is not auth.
- Actually terminating the suite-owned API, not mocking a response, left the
  default visible under its original saved label and disabled custom requests.
  Restart plus manual Retry restored API queries and the **149-report** selection.
- An initial CARROTS URL during an actual outage displayed no unrelated default;
  restart/Retry returned that selection's own **241-report** all-year result.

The suite temporarily trusts its self-signed certificate only in the dedicated
local test config. No OS trust store was modified. Normal browser checks do not
bypass certificate verification. Screenshots of the cross-origin and actual-outage
states were inspected. All suite-owned helper processes were stopped; the ordinary
local preview/backend are separate. This does not verify public TLS certificates,
real hosted origins, a minute-long provider wake or rollback to a different deploy.

## Remaining Acceptance and Next Step

Docker/Podman were not found, including an approved outside-sandbox check; WSL
reported that it was not installed. Therefore the candidate image has **not** been
built, its Linux SQLite/runtime behavior is unverified, and its image size/security,
startup cost and container memory are unknown. No Linux runtime was installed.
The base matches the locally validated Python patch, but is not a current-security
approval; review maintained runtime/base updates before public use.

No new p95/CPU/peak-memory claim is made. Prior constrained Windows measurements
remain historical. The host must still meet warm default p95 <10 seconds for five
requesters; filtered workloads have no new universal ten-second target. New Linux
and actual hosted measurements must distinguish network/wait, rejected requests,
process/container memory and cold wake from warm work.

**Recommended next step:** make a separately approved Linux container runtime
available and run the prepared build/readiness/parity/resource checks before any
public deployment. Then, after the relevant approvals, establish account/repository
eligibility, publish the pinned artifact/reviewed source, provision only confirmed
$0 resources, and execute the actual hosted acceptance/rollback checklist in the
proposal. A real card/charge requirement is still a stop-and-review condition.

The manual Retry path is locally verified; an actual idle Render wake is not.
No remote fetch, GitHub Pages publication, quota exhaustion, provider rollback or
portfolio integration was performed. The earlier upstream core/test-publication
and original builder-permission issues remain separate. The teaching/resume/Flex
completion reminders remain pending; Slice 6 filters/parallel coordinates or another
project are not part of this MVP approval.

## Evidence

Ignored records: `generated/deployment/unit-results.json`, `api-results.json`,
`frontend-unit-results.json`, `browser-results.json`, `local-https-server.log`,
`screenshots/`, the pinned archive/local installation and Linux wheel downloads.
The existing 22-case browser record is `generated/frontend/e2e-results.json`.
No test-trace or private test key is a source-controlled artifact.

FDA reports are not unique people, causation, incidence, relative risk or
product-safety conclusions. Existing saved-snapshot and interpretation labels remain.
