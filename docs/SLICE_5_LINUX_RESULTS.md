# Slice 5B Follow-Up: Local Linux Checks

Subsequent authorized maintenance refreshed the container/runtime and repeated its
checks; see [runtime refresh results](SLICE_5_RUNTIME_REFRESH_RESULTS.md). This file
retains the original Python 3.14.2 image and its measurements as historical evidence.

Verified October 21, 2026, after Abdul installed Docker Desktop and WSL2. This
continues the approved **local deployment preparation**, not public deployment or
completion of Slice 5. No Render service, GitHub Release/Pages publication,
portfolio edit, account/billing change, commit or push was performed by this work.

## Setup Status

- Connected GitHub metadata now confirms `Abdul-RahmanSayed/Project-Lab` is public,
  with `development` as its default branch. The earlier 404 is historical, not the
  current repository-status conclusion. This does not constitute a secret/history audit.
- Abdul reports creating a Hobby Render account and subsequently removing its
  attached payment method. No authenticated inspection of billing, remaining quotas,
  account eligibility or existing resources was performed. Confirm those at provisioning.
- Docker Desktop 4.96.0, Engine 29.9.1, Linux/amd64; WSL reports Ubuntu/default
  version 2. Docker's engine was started locally, without installing more software.

## Package and Runtime

The unchanged candidate Dockerfile built successfully from the allowlisted context
and the existing ignored local archive. Its pinned dependencies installed on Linux,
the installed package extracted/validated the five-file release, and the non-root
serving process started without the FDA checkout, raw pages or analysis libraries.
The downloader's real GitHub Release path remains untested: no asset was published.

- Local image: `project-lab-api:slice5-check-20261021`.
- Image ID: `sha256:ad104bcd125ab2bde2e42e0df4df615093d13de7ce8e31aef3cbdb8524a447c8`.
- Docker-reported image size: **321,206,754 bytes / 321.21 MB / 306.33 MiB**.
  This is not a measured registry transfer size or total Docker build-cache use.
- Python **3.14.2**, SQLite **3.40.1**. SQLite differs from the earlier Windows
  runtime's 3.50.4; the checked database opened and the fixtures below passed.
- Release remains `fda-release-sha256:18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194`.
- Database SHA-256 before and after work:
  `bdfd771ede151a2784a83ff1e9ba1faad727491cce2bddf73a0499521b4d475f`.
  Installed query-code bytes match the existing release/local query pin.

The container used UID/GID 10001, a read-only root filesystem, dropped capabilities,
no-new-privileges and a 64-process/thread cap. All five release files had mode 0444
and were non-writable by the serving user. An attempted write through a read-only
SQLite connection was rejected. These checks are not a vulnerability/security scan.

## Correctness

Eleven overview fixtures match **all fields** of the saved independent Python
reference, using its existing mean tolerances: overall, 2024, case-insensitive
CARROTS, 2024-2026 CARROTS, empty selection, literal `%`, `_`, `+`, partial 2026,
Unicode casefold input and a substring retaining a trailing space. No fresh raw-page
rehash, upstream CLI execution or full original parity suite is claimed.

The default remained 97,652 reports, the year/product selection 149, all-year
CARROTS 241, literal plus 1,811, underscore 2 and actual calendar year 2026 24.
The saved payload answered only the exact default; changed selections used SQLite.
HTTP requests with a different release ID returned 409.

Paging matched **834 report IDs across 14 page requests**. Pagination was exhausted
for the seven fixtures with at most 300 reports; only the first 100 IDs were checked
for each larger fixture. Nine sampled retained report details matched the reference.
This is not a fresh exhaustive replay of Slice 3's 1,530-page check.

## Constrained HTTP Measurements

The whole test container was limited to **0.1 CPU and 512,000,000 bytes RAM**, with
no swap. The observed Linux controls were `cpu.max = 10000 100000` and
`memory.max = 512000000`; throttling was active. These use the published Free
compute figures, not an emulation of Render's hardware, scheduler or proxy.
[Render compute](https://render.com/docs/compute-plans),
[Docker resource limits](https://docs.docker.com/engine/containers/resource_constraints/).

Five-client closed-loop waves used new host-loopback HTTP connections. Each timer
starts before executor submission and ends after reading the complete body,
including dispatch/scheduling wait and HTTP/SQL/encoding/transfer. This is warm local
HTTP, not browser rendering, public HTTPS/internet transfer, service wake or growing
arrival queues. The existing prepared default is the only reused response; no
general cache, coalescing, pending-job queue or eviction policy was introduced.

| Scenario | Successful / total | p95 | Maximum |
| --- | --- | --- | --- |
| Default, ten five-client waves | 50 / 50 | **26.62 ms** | 28.72 ms |
| Repeated uncached CARROTS, two waves | 10 / 10 | 2,965.56 ms | 2,965.56 ms |
| Mixed uncached, two waves | 10 / 10 | 2,201.34 ms | 2,201.34 ms |
| Defaults mixed with filters, two waves | 10 / 10 | 800.69 ms | 800.69 ms |
| Defaults arriving during five SQL requests | 5 / 5 | 195.68 ms | 195.68 ms |
| Those five background SQL requests | 5 / 5 | 2,698.45 ms | 2,698.45 ms |

The revised **default p95 <10 seconds** gate passes locally. The uncached samples
are small representative fixtures, not a new universal filtered-query threshold.
Nearest-rank p95 for ten observations is also their maximum. These are not controlled
before/after comparisons with the earlier Windows timings.

Ten simultaneous uncached requests produced five successes and five HTTP 503 busy
responses, all recorded rather than hidden in successful-only timing. Five SQL jobs,
no application waiting queue and the 30-second budget remain unchanged. A raw TCP
disconnect was exercised without an ensuing process failure; this does not measure
cancellation delay or prove instantaneous worker/slot release.

- Server process resident high-water mark: **108,416 KiB / 105.88 MiB**.
- Container-accounted peak: **216,211,456 bytes / 206.20 MiB**, including page cache
  and temporary inspection processes, not just the API or the entire WSL VM.
- No recorded memory-limit/OOM events; graceful stops exited 0.
- Initial Docker-start-through-first-readiness observation: **11.78 seconds**.
  Local restart readiness polling took **8.85 seconds**, starting after the Docker
  start command returned. These are not equivalent timers or provider wake times.
- Restart retained the same release and 97,652-report default. This is same-image
  local restart, not a rollback to a different deployment or a genuine idle wake.

The harness stopped and removed only its own test container. The image and Docker
Desktop remain available locally. Evidence is ignored at
`generated/deployment/linux-check-20261021/results.json` and `container.log`.

## Remaining Work

The candidate base/runtime is still not approved for public security/currentness.
Review maintained Python/base/dependency updates before public use, preserving the
checked data/policy/query pins and testing any runtime change separately. No silent
upgrade, new snapshot or data rebuild was made to obtain these results.

Before publication: review the source/history and the uncommitted deployment work,
confirm account-specific no-card/Free eligibility and quotas, then obtain the relevant
approval for artifact/source publication and provisioning. Real hosted TLS/origins,
paired release compatibility, fallback, five-client p95/memory, genuine idle wake,
rollback and eventual separately approved portfolio integration are still pending.

No full frontend/API regression rerun was needed or claimed for this test-only
follow-up. Their earlier local HTTPS/browser evidence remains historical. Reproducibility
is the pinned local working tree plus this checked image/data, not a CI/source-only
rebuild or supply-chain guarantee. The upstream core/test-publication questions and
original builder permissions remain separate unresolved issues. Completion and the
teaching/resume/Flex reminders remain pending.
