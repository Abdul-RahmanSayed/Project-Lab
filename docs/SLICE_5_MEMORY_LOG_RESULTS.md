# Slice 5: Opt-In Memory Log and Browser Recovery

October 21, 2026. Abdul authorized restoring browser access and using a small,
opt-in memory log to continue verification without paid tooling. The diagnostic
is implemented and checked locally. The October 21 hosted follow-up below records
the subsequently pushed/deployed revision and measured counters. The October 23
recovery record confirms diagnostic disable/restart and controlled outage recovery;
the recovery record also confirms natural idle sleep/wake. Portfolio acceptance
and final completion remain open.

## Change

The deployment launcher accepts `FDA_MEMORY_LOG=1` on Linux. Its default is `0`,
which returns the original app without a wrapper or memory probes. Enabled output
is limited to startup, the first 200 FDA API requests and graceful shutdown: at
most 202 JSON lines per worker lifetime. Health/readiness requests are excluded.
There are no timers, background threads, new endpoints or dependencies.

Each line identifies `event=fda_memory`, phase, PID, checked release, elapsed
uptime, request-sample count, process resident-memory high-water and available
cgroup v2 current/peak/limit counters, in bytes. No request URL, search, report
content or credentials are recorded. Measurement/output failures cannot replace
the API response or swallow the original exception/cancellation.

The cgroup path is resolved from Linux membership/mount information and checked
against the worker PID. Unsupported, inaccessible, unrelated or unavailable
counters are `null`, never presented as zero. The logger does not reset peaks or
change limits. The existing database, policy/query/schema pins, raw substring
search, normalization, counting, ages and request admission/deadlines are unchanged.

## Local Verification

- Nine focused tests pass on Windows and in the installed Linux image. An initial
  sandboxed Windows run stalled during event-loop setup and was interrupted; the
  subsequent outside-sandbox run passed. This is not recorded as an API defect.
- All 12 existing API regression tests pass inside the installed Linux image,
  using disposable copies for fault injection. The existing Starlette/httpx
  deprecation warning remains visible.
- All 11 bounded overview fixtures match the existing independent Python oracle;
  report checks cover 834 IDs, 14 page requests and nine sampled details. This is
  not a fresh original-CLI run or exhaustive coverage of all reports/searches.
- All 12 previously recorded data/policy/query/dependency invariant hashes remain
  unchanged. No new archive, release identity or analysis rule was introduced.

The diagnostic image uses the existing pinned Python 3.14.8/Bookworm base and
serving dependencies. Its local manifest-list digest is
`sha256:acfc56daf7d3a5c8aa4e17feeeff7db098508c53952c993a3992cd8377696d43`;
Linux/amd64 manifest is
`sha256:14fed8a78da34967f77524f509c35d742ed4ad522eff19bae841a182404eaed6`.
The application wheel hash is
`3bdb6a63365f0f8debcc69da462875669d59113a2ae411ae830a8be5d20c7e5e`.
These identify this local build, not a future Render-built image.

## Constrained HTTP Results

The existing harness ran with logging enabled, 0.1 CPU, 512,000,000 bytes RAM,
no swap, non-root identity and read-only filesystem. Timing includes dispatch
through full response receipt over local loopback HTTP. Logging overhead is
included; this is not a controlled logging-on/off comparison or hosted result.

| Scenario | Success / requests | p95 | Maximum |
| --- | --- | --- | --- |
| Default, ten five-reader waves | 50 / 50 | 85.74 ms | 86.11 ms |
| Repeated uncached | 10 / 10 | 8,145.11 ms | 8,145.11 ms |
| Mixed uncached | 10 / 10 | 5,397.09 ms | 5,397.09 ms |
| Defaults mixed with filtered work | 10 / 10 | 1,893.25 ms | 1,893.25 ms |
| Ten-request SQL burst | 5 / 10; five busy 503 | 5,999.86 ms, all requests | 5,999.86 ms |
| Default during SQL work | 5 / 5 | 989.61 ms | 989.61 ms |

Small samples are representative fixtures, not a universal filtered latency
promise. Closed-loop waves do not test growing arrival queues. No general cache
or cache eviction exists; the exact prepared default is reused as before.

The log contains 142 lines across two process lifetimes: 138 request samples,
two startups and two graceful shutdowns. Maximum logged process RSS high-water
was **105,607,168 bytes (100.71 MiB)**. The independent `/proc/1/status` sample
reported **103,924 KiB (101.49 MiB)**; these Linux accounting interfaces are not
claimed byte-identical. Logged cgroup peak was **136,331,264 bytes (130.02 MiB)**,
matching the independent harness cgroup peak exactly. The verified cgroup limit
was 512,000,000 bytes. Memory high/max/OOM/OOM-kill events were zero; both recorded
shutdowns exited zero without an OOM kill. The owned test container was removed.

Ignored evidence:

- `generated/deployment/memory-log-linux-1/results.json`
- `generated/deployment/memory-log-linux-1/container.log`
- `generated/deployment/memory-log-regressions/regression-results.json`

## Interpretation and Limits

Process RSS high-water covers the worker lifetime, including startup, rather than
only one query. Cgroup peak covers that group's lifetime and can include descendants
and charged file cache; it is not interchangeable with worker RSS. A leaf group's
`memory.max` is not proof of the effective ancestor/provider limit. Counters may
remain unknown on a host with different mounts, permissions or cgroup v1.

The request cap limits output and per-request work. It does not establish a
continuous monitoring service. Graceful shutdown can report a later lifetime peak,
but abrupt process termination may omit that line. No reset or attribution to an
individual reader is claimed. Linux counter semantics are described by the
[kernel cgroup v2 documentation](https://docs.kernel.org/admin-guide/cgroup-v2.html)
and [getrusage reference](https://man7.org/linux/man-pages/man2/getrusage.2.html).

## Browser Recovery and Next Step

After Abdul restarted Chrome, reopened its extension and signed back into Render,
browser control and screenshots worked. Public default charts, the 149-report
CARROTS/2024-2026 selection and a report detail were inspected. An invalid-release
shared URL showed an explicit warning and labeled saved default, with Apply
disabled; its default numbers were not presented as the rejected product query.
See the [hosted results](SLICE_5_HOSTED_RESULTS.md) for evidence boundaries.

A viewport override did not apply in the restored session, so this follow-up
adds desktop screenshots only. It does not supersede earlier mobile-width DOM
checks with new mobile visual evidence. Dashboard events did not establish a
sleeping state, and reopening the default page was already ready; natural idle
wake and actual unavailable-backend browser recovery remain unverified.

The original local handoff was: Abdul retains commit/push ownership. After he pushes the reviewed change, record
its exact commit, manually deploy it to the existing Free service with
`FDA_MEMORY_LOG=1`, run the bounded hosted checks, and inspect its memory lines.
Then set the flag back to `0` and verify the restarted service. No Pages rebuild
is needed for this backend-only change. Auto-deploy remains off. No paid tooling,
new service, portfolio edit or completion reminder is authorized by this step.

## October 21 Hosted Measurement; October 23 Evidence Review

Abdul pushed the complete change as
`5a76fbec6a1f51bbbdd490e9f1bfdb50668ebf55`. The preceding `d6745d1` omitted
four new files, including the imported logger; it was caught before deployment
and was never selected for a Render deployment. The complete revision was
manually deployed with `FDA_MEMORY_LOG=1` to the existing Free service as
`dep-dbc825bbc2fs73bk2t50`; the dashboard reported success in 35.1 seconds.
The build fetched and validated the existing checked archive and retained its
release ID. No Pages build or database/policy/query pin changed.

The bounded HTTPS harness completed successfully. Metadata/provenance, allowed
and disallowed Origin headers, the 409 release mismatch and all 11 overview
fixtures passed. Report/detail coverage remains 834 IDs, 14 page requests and
nine sampled details, with the same partial-pagination limits as earlier runs.

| Hosted HTTPS scenario | Success / requests | p95 | Maximum |
| --- | --- | --- | --- |
| Default, ten five-reader waves | 50 / 50 | **151.93 ms** | 155.48 ms |
| Repeated uncached | 10 / 10 | 2,524.65 ms | 2,524.65 ms |
| Mixed uncached | 10 / 10 | 1,700.36 ms | 1,700.36 ms |
| Defaults mixed with filtered work | 10 / 10 | 901.93 ms | 901.93 ms |
| Ten-request SQL burst | 5 / 10; five busy 503 | 2,002.17 ms, all requests | 2,002.17 ms |

The warm five-reader default passes the p95-below-ten-seconds requirement with
logging enabled. This includes verified HTTPS and complete response receipt,
not browser rendering or sleep/wake latency. Small filtered samples establish
no universal filtered SLA, and these are not controlled speed comparisons.

The visible Render application log retained 50 JSON counter lines, ending at
request sample 127 / worker uptime 48.908 seconds. At that point the worker's
process RSS high-water was **104,816,640 bytes (99.96 MiB)** and its resolved
cgroup lifetime peak was **93,536,256 bytes (89.20 MiB)**. The cgroup reported
`memory.max=536870912` (**512 MiB**). The retained final high-water readings
include the earlier work in this process/group lifetime even though the UI
only exposed the last 50 lines; no claim of complete log export is made.

Both observed peaks are below the reported group limit; RSS is also below the
baseline's 350 MiB process target. Process RSS and cgroup charging use different
accounting rules and are not interchangeable or necessarily ordered. These
readings are actual host observations for this bounded workload, not an
independent audit of ancestor/provider enforcement, OOM events or future load.
No independent hosted OOM-event counter or shutdown sample was captured.

Ignored evidence is under `generated/deployment/hosted-memory-20261021`:
`results.json` and `render-visible-logs.txt`. The attempted clipboard export
produced an empty `render-copied-logs.txt`; it is not measurement evidence.
These files were inspected again on October 23 without rerunning the workload.

The previous session reached editing the diagnostic flag to `0` but did not
complete saving/restarting it. On October 23, inspection confirmed it was still
`1`; it was saved as `0` and applied by successful same-image deployment
`dep-dbdretjrjlhs7384useg`. The fresh public filtered query matched 149/123/26.
The [recovery follow-up](SLICE_5_RECOVERY_RESULTS.md) records cleanup, controlled
outage behavior, provider routing limitations, restoration and new mobile evidence.
The same record now confirms natural idle sleep/wake. Portfolio approval and
final completion remain ahead.
