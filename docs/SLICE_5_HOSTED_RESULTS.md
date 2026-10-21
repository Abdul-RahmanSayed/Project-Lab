# Slice 5C: Hosted Acceptance in Progress

October 21, 2026. **Partial backend milestone, not completed Slice 5 acceptance.**
The public data attachment, one Render Free API and GitHub Pages frontend exist.
Bounded actual-browser flows and a same-data backend rollback rehearsal pass.
Hosted peak-memory observation, genuine idle wake and complete visual verification
still need their recorded checks. Restoration is a same-data rehearsal, not a
cross-version migration test.
The portfolio is unchanged.

## Authorization and Account Checks

Abdul explicitly approved one Render Free backend, Pages publication and bounded
hosted tests. After discussing the difference between openFDA's general CC0 terms
and unresolved third-party terminology questions, he chose to continue and
separately approved the public checked database attachment. This records his
decision, not a finding that every licensing or security question is resolved.

The actual Render workspace showed Hobby, no payment method, zero existing services,
no pending charges and unused allowances of 750 free hours, 5 GB bandwidth and
500 build minutes. The new service creation form was explicitly changed from its
paid default to **Free: $0/month, 0.1 CPU, 512 MB RAM**. No paid disk, database,
add-on, domain, preview service, account token or keep-awake service was created.

## Published Artifacts and Service

- [Snapshot attachment release](https://github.com/Abdul-RahmanSayed/Project-Lab/releases/tag/fda-snapshot-18446003726e),
  labeled pre-release because end-to-end acceptance is unfinished.
- Fixed source checkpoint: `db52f77a50df70282157aa944f6294fbeede206b`.
- Attachment: `fda-18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194.tar.gz`,
  17,855,778 bytes. GitHub's published SHA-256 matches the reviewed lock:
  `3895e5b06e9ea5e7432ed7e0a8c58efe85024b2fda32ac5f235d25319d7e6ba1`.
- [Hosted API](https://project-lab-fda-api.onrender.com/readyz), service
  `project-lab-fda-api`, Virginia (US East), Docker from `deployment/Dockerfile`.
- Render deployment: `dep-dbc6pnuq1p3s73cg4b4g`, service
  `srv-dbc6pnmq1p3s73cg4aa0`. The dashboard reported a successful first deployment
  lasting 43.2 seconds. This is not an idle-wake measurement.
- Build logs confirm the fixed public archive was fetched and all existing checked
  release validation completed. The serving startup retained the same release ID.
- Persistent settings confirm auto-deploy **Off**, PR previews **Off**, health check
  `/readyz`, no registry credential and no Docker-command override.

The exact database, source/policy/query/schema pins and serving dependency lock
remain unchanged. The database remains
`bdfd771ede151a2784a83ff1e9ba1faad727491cce2bddf73a0499521b4d475f`.
No raw-search, normalization, counting, age, cache, admission or deadline behavior
was changed. Render built its own wheel/image: do not claim byte identity with the
local image or a source-only FDA rebuild guarantee.

## Bounded Hosted API Checks

`tests/check_hosted.py` reuses the existing bounded independent-Python-reference
fixtures and timing/statistics conventions. The client uses ordinary verified HTTPS,
reads the complete bounded response body, opens new connections and includes time
from before worker submission through full-body receipt. No certificate bypass,
provider keep-awake polling, general cache or queued application work was added.

The first attempt stopped after two successful HTTP requests because the new test
helper incorrectly expected identity fields inside the analysis-only overview
fixture. The helper was corrected to compare provenance against the checked
frontend metadata bundle; query values still compare with the independent Python
reference. A new offline regression covers the identity check. No application or
data change was made to fix that test failure.

The second run passed readiness, selected-release metadata/provenance, allowed and
disallowed Origin response headers, and an explicit 409 release-mismatch response.
These header checks are not yet an actual cross-origin browser test.

All 11 complete overview fixtures matched: overall, year, raw-product, combined,
empty, literal punctuation, actual 2026, Unicode casefold and trailing-space cases.
Checks covered **834 report IDs across 14 page requests and nine sampled details**.
Pagination was exhaustive only for the seven fixtures with at most 300 reports;
larger fixtures checked their first 100 IDs. This is not a fresh original CLI run,
every possible search or the earlier exhaustive 1,530-page suite.

| HTTPS scenario | Success / requests | p95 | Maximum |
| --- | --- | --- | --- |
| Warm default, ten five-reader waves | 50 / 50 | **169.06 ms** | 190.52 ms |
| Repeated uncached CARROTS, two waves | 10 / 10 | 2,822.87 ms | 2,822.87 ms |
| Mixed uncached selections, two waves | 10 / 10 | 1,694.85 ms | 1,694.85 ms |
| Defaults mixed with filtered work, two waves | 10 / 10 | 799.64 ms | 799.64 ms |
| Ten-request SQL burst | 5 / 10; five HTTP 503 | 1,963.34 ms, all requests | 1,963.34 ms |

The warm five-reader default **p95 <10 seconds** requirement passes for these hosted
HTTPS requests. Filtered samples are deliberately small, and their nearest-rank
p95 equals maximum at ten observations. No universal filtered latency threshold
was introduced. Busy responses are retained, not counted as fast successes.
Closed-loop waves do not establish growing-queue capacity or public abuse resistance.
These are not controlled before/after comparisons with earlier desktop/container runs.

Ignored evidence is under `generated/deployment/hosted-20261021-first` and
`generated/deployment/hosted-20261021-run2`. The latter contains the successful
acceptance JSON and all measured request records. The original reference file's
SHA-256 is `029273afe37b692cac69f0161c13c10d5b8c96a9f8e36c976d0e8111daa1b35b`.

## Frontend Publication and Browser Checks

The new `.github/workflows/pages.yml` is manual-only, uses verified fixed official
action commit IDs and the locally checked Node 24.13.0, installs locked dependencies,
runs frontend tests and the checked-bundle/typecheck/build path, and publishes only
the built website. Its source input must be a full reviewed commit ID. API origin
input is passed through the existing HTTPS-origin validator; neither input is
interpolated as executable shell code. A public `deployment.json` records the selected
frontend source, API origin and exact data release for pairing/rollback checks.

No database/archive is included in the Pages artifact. The existing saved overview
is not replaced or repinned. Node/action pinning here is not a new full build-tool
security clearance or public-source FDA preparation guarantee.

Local checks passed: structured YAML/manual-trigger/action-pin/permission/artifact
path checks; eight offline hosted-client tests; 20 frontend unit tests; frontend
bundle/typecheck/build; all 12 previously recorded data/policy/query/dependency
invariant hashes unchanged. No hosted full-browser or rollback result follows.

Abdul committed/pushed the four deployment-only files himself as
`88430e716be101a09a3a61bd487dabc119021fec`:
`.gitattributes`, `.github/workflows/pages.yml`, `tests/check_hosted.py` and
`tests/test_hosted.py`. The agent has not committed or pushed.

[Manual Pages run 39565823387](https://github.com/Abdul-RahmanSayed/Project-Lab/actions/runs/39565823387)
succeeded in 1 minute 9 seconds: build 20 seconds, deploy 37 seconds, 20/20 frontend
unit tests passed. Workflow code came from `88430e7`; the explicit source input was
the reviewed application checkpoint `db52f77a50df70282157aa944f6294fbeede206b`.
The public [FDA Explorer](https://abdul-rahmansayed.github.io/Project-Lab/#/fda)
and its `deployment.json` confirm that exact source, the actual Render origin,
unchanged release/archive hashes and Node v24.13.0.

The runner warned that the pinned Pages deploy action and nested upload-artifact
action declare Node 20 but are forced onto Node 24. They executed successfully;
this is a recorded maintenance warning, not evidence that the frontend ran Node 20
or that all action compatibility/security questions are settled.

Bounded real Chrome checks from the Pages HTTPS origin passed:

- API ready, default 97,652 reports, five chart regions, 181 data marks and 25
  nonzero annual marks. At the default 1,507-pixel viewport, document width was
  1,492 pixels, without horizontal page overflow.
- CARROTS / 2024-2026: 149 reports, 123 valid ages, 26 missing/invalid ages;
  annual table 122 / 27 / 0 and 126 age-table rows.
- Reports: 25 rows, distinct next page, previous page restores the first ID;
  100-row sizing followed by 49 final rows with Next disabled.
- Detail for `2024-CFS-003758`: original SUSPECT name, canonical term, current-search
  match, reactions/outcomes and saved source page/position are visible; Escape closes.
- Copy-view confirmation and actual shared URL retain release, years, raw product,
  tab and page size. Reload restores the selected tab and 149-report selection.
- At a 390-pixel emulated viewport, all five chart bounds stay within the viewport
  and document width is 375 pixels. Mobile filter expansion/application collapses
  again; a known nonexistent selection returns zero and an explicit empty message.
  This is viewport emulation, not a physical touch-device test. Override was reset.

Screenshot capture timed out in browser tooling. DOM/geometry and working controls
are evidence for the checks above, not substitute screenshots or complete hosted
visual/accessibility verification. Initial loading observations are not a measured
idle-wake result. The existing full local browser suite was not rerun as a complete
hosted suite.

## Hosted Resource Observation Limit

The actual Free service's Metrics page explicitly requires a paid upgrade for
memory/CPU usage charts. No upgrade was made. Its memory limit label is 512 MB;
its CPU limit label is 0.15 CPU, unlike the creation form's 0.1 CPU. Neither label
independently measures enforcement or peak consumption. Hosted peak RSS/cgroup
usage remains unmeasured; the earlier constrained local results are not silently
substituted for hosted evidence. A minimal bounded log-only diagnostic is the
recommended follow-up if this gate cannot be satisfied with existing free tooling.

Abdul subsequently authorized the small opt-in log. Its implementation and local
verification are recorded in [memory log results](SLICE_5_MEMORY_LOG_RESULTS.md):
nine focused tests, 12 installed Linux API regressions and bounded HTTP parity
pass. Local cgroup peak with logging was 130.02 MiB under 512,000,000 bytes.
The change is not yet pushed/deployed; this does not establish Render memory use.

### Restored Browser Follow-Up

After Abdul restarted Chrome/reopened the extension and signed into Render,
browser control and screenshot capture worked. The underlying disconnection
cause is unproven. Desktop default charts and the 149-report CARROTS/2024-2026
selection rendered, and report `2024-CFS-003758` opened with retained fields and
source position. No browser console errors were observed in the default check.

A shared URL with an invalid release and CARROTS showed the explicit message
that the view belonged to another snapshot and no custom query had been sent.
Apply was disabled. It displayed 97,652 saved-default reports labeled as all
suspect products, not as the rejected CARROTS selection. This verifies an invalid
shared-view state, not an actual unavailable-backend test for a valid custom view.

Screenshots are retained under ignored `generated/deployment/screenshots`:
`hosted-default-desktop.png`, `hosted-invalid-release.png` and
`hosted-report-detail.png`. The attempted 390-pixel override did not apply in
this restored browser session and was reset. The associated capture is desktop,
not new mobile evidence. Earlier mobile DOM checks remain separately qualified.

Render Events did not expose a sleeping-state observation. After another idle
interval the default browser view was already ready, so no genuine cold wake or
unavailable-backend fallback/recovery is claimed from this follow-up.

## Backend Rollback Rehearsal

One manual deployment of the pushed deployment/test-only checkpoint `88430e7`
succeeded: `dep-dbc75pon74is73fk2th0`, dashboard duration 18.3 seconds. Existing
build layers were cached. The real public frontend still returned the exact default.
Render then reported no configuration changes relative to the original deployment;
its Rollback control restored `dep-dbc6pnuq1p3s73cg4b4g` as a new successful live
deployment `dep-dbc76gks728c73e83o60` from `db52f77`, duration 10.6 seconds.
An actual browser CARROTS/all-years request after restoration returned 241 reports
with API ready. The frontend remains pinned to `db52f77` and the same data release.

This exercises the provider's restore mechanism with a compatible static frontend,
not recovery from an intentionally broken application, changed data/schema or
destructive migration.

## Frontend Artifact Recovery Rehearsal

Only the Pages `deploy` job was re-run, using the existing successful website
artifact: run `39565823387`, attempt 2, deployment job `119114160612` succeeded in
nine seconds (overall attempt 16 seconds). This was not a second application build
or fresh second frontend-test run. The public manifest after republishing retained
the exact `db52f77` source, approved Render origin, release ID and archive checksum.
Together with the restored backend, this rehearses restoring a compatible pair;
it does not test an intentionally broken or differently versioned frontend.

Seven actual public files were downloaded to ignored
`generated/deployment/hosted-20261021-frontend`: index, manifest, active JS/CSS, two
fonts and font licenses. All six content files match the local reviewed build
byte-for-byte; the seventh is the workflow-generated manifest. An obsolete local
build JS file was deliberately excluded. Recovery ZIP
`generated/deployment/hosted-20261021-frontend.zip` has SHA-256
`be24ee8bd629fd5340d62c158d13f1d2c1e05a30cb65eb07d836fe46ad4c2aff`.
The ZIP and downloaded files remain ignored, not checked into source control.
The workflow artifact expires after one day; it is not indefinite provider retention.
The local copy, fixed source/workflow inputs, public checked data archive and recorded
service configuration are the retained recovery evidence, not a guarantee that
provider history or this local disk remains available forever.

## Remaining Acceptance

### Idle-Period Observation, Not Verified Cold-Browser Acceptance

After the post-rollback CARROTS query succeeded, the test browser tab was closed.
At 08:11:11 UTC the agent began its no-backend-request interval. Static Pages files
and provider dashboard checks during the interval did not intentionally contact
the API. The frontend source has no recurring API polling/keep-awake timer.
Other public visitors and provider health checks were not controlled.

At 08:29:21.759 UTC, a single HTTPS `/readyz` request returned HTTP 200 JSON with
the correct release after **12,688.30 ms**. Timing is a .NET Stopwatch around one
PowerShell HTTPS request, including connection setup, not browser rendering,
default-overview latency, p95 or a controlled comparison with the earlier client.
The intervening desktop idle period was not protected by the historical profiler's
standby guard. No new background polling or retry loop was added.

The browser lost its debugging connection during the idle wait. Existing-tab
reconnection failed; a fresh dashboard-tab attempt timed out and reset the browser
automation session, and one post-reset attachment still failed. No provider
asleep-state observation or actual cold-browser fallback/recovery was obtained.
The delay is consistent with wake-up, but does not prove it: genuine provider
sleep and browser acceptance remain open. Screenshot/DOM failures are tooling
limitations, not evidence of an application defect. Restore the browser connection
before another bounded idle/browser trial; do not repeat blind requests or upgrade.

### Open Gates

- Complete hosted visual verification and honest failure/version fallback checks;
  the bounded browser flows above do not imply every interaction was exercised.
- Record provider resource observations with honest sampling/peak limits; no actual
  hosted memory peak has been measured yet.
- Observe genuine idle sleep and cold recovery without pings; distinguish warm p95
  from wake-up and use bounded attempts/manual Retry.
- Obtain the separate portfolio-edit approval, add/test its narrow Live Demo link
  and confirm the portfolio home makes no FDA API/data requests.

Native-library advisory coverage, third-party terminology clarification and upstream
test-publication/source-only rebuild questions remain explicitly unresolved. No
completion/teaching/resume/Flex reminder is due yet. These are FDA adverse-event
reports, not unique people, causation, incidence, relative risk or product safety.
