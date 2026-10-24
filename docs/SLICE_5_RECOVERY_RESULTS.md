# Slice 5: Diagnostic Cleanup and Hosted Recovery

October 23, 2026. This continues the approved bounded tests on the existing
Render Free service and Pages frontend. It does not mark the MVP complete.

## Selected Version and Diagnostic Cleanup

The backend is complete revision `5a76fbec6a1f51bbbdd490e9f1bfdb50668ebf55`.
Pages remains the reviewed `db52f77` frontend; the contract, release and analysis
rules match. The [October 21 memory/HTTPS results](SLICE_5_MEMORY_LOG_RESULTS.md)
were reviewed from their saved files rather than rerun as a new whole suite.

On resuming, the actual provider flag was still `FDA_MEMORY_LOG=1`. It was changed
to `0` using Save and deploy, reusing the existing image. Deployment
`dep-dbdretjrjlhs7384useg` succeeded in 11.1 seconds with the same `5a76fbe`
source. The saved environment page shows `0` and the Free service live. A fresh
browser query returned CARROTS/2024-2026: 149 reports, 123 valid ages and 26
missing/invalid ages. The database, release and policy/query pins were unchanged.

## Actual Unavailable-Backend Test

The existing service was briefly suspended through Render's reversible control.
Events record Service suspended / Suspended by you at 3:38 PM EDT, then Service
resumed / Resumed by you at 3:39 PM EDT. No other service or paid resource was
created. This is a controlled provider outage, not natural idle sleep.

Three public-browser states were inspected:

- A fresh default page displayed the labeled 97,652-report saved overview while
  Connecting, then an unavailable message and manual Retry after its bounded
  attempts. Apply stayed disabled until connection recovery.
- A fresh valid CARROTS/2024-2026 shared selection showed its requested filters,
  no result totals, an unavailable message and Retry. It did not substitute
  the unrelated all-year saved default.
- An already loaded CARROTS/2024-2026 result followed by applying
  `no-match-7c46ba` failed visibly. The 149 old reports retained the CARROTS label
  and explicit Previous result state rather than being relabeled as the new query.

Quota exhaustion was not induced. The previously measured busy responses and
existing bounded local fixtures remain the evidence for overload/quota-related
handling; the controlled suspension is the evidence for actual host unavailability.

## Restoration and Provider Limitation

Resume alone did not immediately restore all observed routes. A readiness request
returned checked HTTP 200, while a filtered request still returned provider HTTP
503 HTML titled Service Suspended. A later request with Cache-Control: no-cache
still returned `x-render-routing: suspend-by-user` and `cf-cache-status: DYNAMIC`.
This does not establish ordinary browser caching as the cause. The provider Events
page recorded the resume; readiness alone was insufficient evidence of recovery.

One Manual Deploy / Restart service action was used; the provider records Service
restarted by you at 3:41 PM EDT. Subsequent HTTPS metadata, prepared default and
CARROTS requests returned HTTP 200 with the checked release and the expected
allowed Origin header. The exact cause of the earlier inconsistent routing is
unresolved. This was an operational recovery with a restart, not proof that Resume
alone always works or a natural idle wake measurement.

Manual Retry then recovered the public pages: default API ready, custom CARROTS
149/123/26, and the formerly failed `no-match-7c46ba` query returned zero with an
explicit empty state and unavailable mean age. No data, retry, query or cache
implementation changes were used to get these results.

## Visual and Mobile Follow-Up

The restored session applied a 390x844 viewport successfully. The filtered overview
rendered all five chart groups, preserved the totals and contained the chart bounds
within the viewport. DOM geometry reported main width 390 and no main descendants
extending outside the viewport. This is browser viewport emulation, not a physical
touch-device or exhaustive accessibility audit.

The report list and detail `2024-CFS-003758` opened at mobile width. The loaded
dialog remained within the viewport, with vertical scrolling and a separate
horizontal product-table scroller. Its first captured opening frame preceded the
detail data; the separately named loaded screenshot is the visual evidence for
the populated dialog. Escape closed it and restored outside focus. The temporary
viewport override was reset after the check.

Ignored screenshots under `generated/deployment/screenshots`:

- `render-memory-off-20261023.png`
- `hosted-outage-default-20261023.png`
- `hosted-outage-custom-20261023.png`
- `hosted-outage-previous-20261023.png`
- `hosted-mobile-filtered-20261023.png`
- `hosted-mobile-detail-loaded-20261023.png`
- `hosted-recovered-filtered-20261023.png` (recovered report list)

Saved visible fallback text is under
`generated/deployment/hosted-memory-20261021/outage-*-20261023.txt`. Generated
evidence remains ignored. No portfolio file, Git commit or push was made.

## Natural Idle Trial

All FDA browser tabs were closed at **19:46:46.762 UTC**. No API requests, frontend
tabs, keep-awake requests or periodic API probes are to be made during the trial.
The earliest planned check is **20:02:46.762 UTC**, sixteen minutes later.
Provider dashboard/static/local documentation work does not intentionally contact
the API. Other visitors/provider traffic are not controlled.

Render documents automatic sleep after 15 minutes without inbound traffic and
roughly minute-long wake. Its documented `/robots.txt` response can be checked
without waking a sleeping Free service. The one pre-trial request at
19:36:36.565 UTC returned the application's 404 JSON, so it did not establish
sleep at that earlier time. [Render Free behavior](https://render.com/docs/free).

The eventual single command-line robots check completed at **20:09:57.486 UTC**,
after more than 23 minutes without agent app/API requests. It received HTTP 403
Cloudflare challenge HTML, not Render's sleep response. No challenge was solved,
protection bypassed or repeated command-line probe added. The dashboard Events
page did not expose an asleep event, so this does not confirm natural sleep.

The first subsequent default browser visit began at **20:10:40.995 UTC**. Its
initial observation at 4.324 seconds showed the 97,652-report labeled saved default
while Connecting. It was still Connecting at 10.952 seconds and API ready at the
next observation, 39.468 seconds after opening. These are observation bounds
including automation overhead, not an exact load time, request p95 or measured
sleep duration. It recovered automatically within the existing bounded attempts.
A fresh browser CARROTS/2024-2026 request then returned 149/123/26.

The saved-first screenshot is `hosted-idle-saved-first-20261023.png`. Provider
application logs showed the old diagnostic process shutting down when the zero
flag deployment went live and did not provide a new explicit sleep/wake event.
This is a passed idle-period browser recovery observation; actual sleep remains
unconfirmed. A later normal Chrome navigation to the same non-waking robots path
read the application's ordinary 404 JSON without the command-line challenge.

One final trial therefore uses the browser for the non-waking check. All FDA
tabs were closed again at **20:21:56.894 UTC**, with the earliest planned browser
check at **20:37:56.894 UTC**. Logging remains off, and there are no keep-awake
requests or changes to retries, policies or service resources. The second trial's
result follows. Portfolio approval and the completion follow-ups remain pending.

### Confirmed Natural Sleep and Browser Recovery

At **20:51:52.153 UTC**, after 29 minutes 55.259 seconds with all FDA tabs closed
and no agent API traffic, a fresh normal Chrome visit to `/robots.txt` displayed:

```text
User-agent: *
Disallow: /
```

This matches Render's documented special response for a sleeping Free service,
which does not wake the worker. The earlier awake application response was 404
JSON. Together these provide affirmative sleep evidence; the dashboard's Live
deployment badge was not used as proof. The quiet interval is not a measurement
of how long the worker was asleep. No standby guard or controlled external-traffic
isolation was used, so timings remain observation bounds.

The first subsequent default visit began at **20:51:59.766 UTC**. Its initial
observation at 3.934 seconds displayed the labeled 97,652-report saved default
while Connecting, with Apply disabled. It was still Connecting at 14.159 seconds
and API ready at the next observation, **46.671 seconds** after opening. No manual
Retry was needed in this trial. The exact instant of readiness lies between those
observations; this is one cold visit, not a p95 benchmark or promise of maximum
wake duration. Slower wakes can still require the existing manual Retry.

A new CARROTS/2024-2026 browser query after recovery returned **149 selected
reports, 123 valid ages, 26 missing/invalid ages and mean 42.95 years**, labeled
API query / saved snapshot. Its shared URL retains the checked release. The
previously inspected contract checks also reject a different release/filter.
No retry, cache, SQL, analysis or resource-setting change was needed.

Ignored screenshots:

- `render-sleep-robots-20261023.png`: affirmative non-waking sleep response.
- `hosted-confirmed-cold-saved-20261023.png`: saved default while Connecting.
- `hosted-confirmed-wake-filtered-20261023.png`: recovered actual filtered result.

The temporary robots tab was closed, the viewport override was reset, and the
working filtered demo was left open. The existing service is resumed and the
diagnostic flag remains zero. No more idle trials or benchmark waves are needed
for this milestone.

## Remaining Acceptance

The bounded hosting checks now cover correctness/identity, warm five-reader
latency, actual memory counters, desktop/mobile browser flows, actual outage
fallback/recovery, confirmed natural sleep/wake and the earlier same-data
backend/frontend restoration rehearsals. Their documented sample/security/
licensing/provider limitations remain; this is not an exhaustive device/load or
cross-schema migration guarantee.

**The overall MVP is not yet complete.** Abdul subsequently approved the narrow
portfolio edit and local checks. The [local integration record](SLICE_5_PORTFOLIO_RESULTS.md)
documents the applied two-line change, passing build/typecheck and bounded
desktop/mobile no-FDA-request checks. Publication remains Abdul's responsibility;
verify the actual public portfolio link and homepage network behavior after that,
then record the final acceptance decision. The teaching, resume and Flex fintech
reminders stay pending until that work is complete.

## Historical Portfolio Proposal, Subsequently Approved Locally

The current FDA entry in the portfolio's
`artifacts/portfolio/src/components/ProjectsSection.tsx` already renders a Live
Demo anchor when `live` has a value. The proposed change is to replace its
`live: null` with `https://abdul-rahmansayed.github.io/Project-Lab/#/fda` and append
this sentence to its description: "Extended with a saved-snapshot Explorer for
interactive filtering and report browsing."

Keep the original take-home attribution, pipeline source link and historical
claims. Use the existing button/anchor; do not embed, import or preload the
Explorer. The anchor itself makes no FDA API/data request when the portfolio
home loads. This source inspection is not a built or hosted portfolio network
test. This proposal was subsequently approved and applied locally as recorded in
the linked integration results. No portfolio commit, push or publication was
performed by the agent.
