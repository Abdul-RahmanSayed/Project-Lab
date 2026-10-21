# Slice 5B: Local Runtime Refresh

Implemented and checked October 21, 2026, after Abdul authorized a small local-only
runtime/build-tool refresh and repeated correctness/resource checks. No deployment,
architecture redesign, service/account creation, artifact publication, portfolio
edit, commit or push was performed. The earlier [Linux results](SLICE_5_LINUX_RESULTS.md)
remain a separate historical checkpoint, not overwritten measurements.

## Scope and Pins

- Remain on Python 3.14 and Debian Bookworm; no Python 3.15 or distribution migration.
- Both Docker stages now use `python:3.14.8-slim-bookworm` at the actual inspected
  Linux/amd64 manifest digest
  `sha256:ddec44f5ab04dd68aaee83d7dc9831c964a4bb9e950c89960e60760373fbf54f`.
- Actual installed OpenSSL: **3.0.22**, Debian `3.0.22-1~deb12u1`. SQLite remains
  **3.40.1**, Debian `3.40.1-2+deb12u2`. Other base-OS packages follow that fixed image,
  not a mutable build-time OS upgrade.
- Builder tools: **pip 26.2.2** and **setuptools 84.2.1**, each with its exact wheel
  SHA-256 in `deployment/build-tools.lock.txt`. Their public PyPI records were not
  yanked and returned no advisory entries at this check. The API's root build
  metadata now requires setuptools 84.2.1; its serving dependencies did not change.
- pip/setuptools are uninstalled from the copied venv after building/extracting,
  and pip is uninstalled from the final base interpreter before serving. Neither
  tool is importable through **either** installed interpreter in the tested final
  filesystem. This is not a claim that stdlib `ensurepip` or bytes in lower image
  layers were eradicated.

Primary references: [Python 3.14.8](https://www.python.org/downloads/release/python-3148/),
[pip metadata](https://pypi.org/pypi/pip/26.2.2/json),
[setuptools metadata](https://pypi.org/pypi/setuptools/84.2.1/json),
[Debian OpenSSL](https://security-tracker.debian.org/tracker/source-package/openssl).

The selected release remains
`fda-release-sha256:18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194`.
All **12 recorded invariant files** matched before/after: the five release files,
deployment release lock, serving dependency lock, source/policy lock and the
query/runtime/schema/preparation modules. The database SHA-256 remains
`bdfd771ede151a2784a83ff1e9ba1faad727491cce2bddf73a0499521b4d475f`.
No repack, data rebuild, policy repin, normalization/count/age change, general cache,
cursor signing, pending queue or new filter was introduced. Windows Python and
existing host virtual environments were not upgraded globally.

## Built Artifact

- Local image: `project-lab-api:runtime-refresh-20261021`.
- Image ID: `sha256:224128ea5299464426d3fa30d902f9ed77ec4295013a2ca3357ebdbcbce5e811`.
- Docker-reported image size: **296,029,745 bytes / 296.03 MB / 282.32 MiB**.
  This is not registry transfer size or total Docker cache/storage use.
- API wheel built inside the image: SHA-256
  `12ea46239f2b4c776475b62de048780e2c5ca007f6c21dfe2cad018ab9b19718`.
  Its package version remains 0.1.0; this is not the earlier wheel's byte identity.
- All **25 installed application Python source files** matched the working-tree
  bytes before and after testing. Build metadata/runtime changed, not API/query code.

## Correctness

The **12 existing API regressions passed on Python 3.14.8 inside the installed
Linux image**. Tests include context-aware pagination/details, literal raw search,
default identity, readiness/shape/version failures, response limits/CORS, overload,
native-SQL timeout/disconnect cancellation and retaining slots until workers exit.
Corruption tests operated on temporary copies; original image data stayed unchanged.

Only the test module and three checksummed pure-Python test wheels were mounted
read-only. No test dependencies were installed into the serving image. That
functional container had a 1-CPU/512,000,000-byte cap and writable temporary space;
it is separate from the performance container below. The pre-existing
Starlette/httpx deprecation warning remains; it was not hidden by upgrading serving
or test libraries. Expected injected release failures logged their error types.

Actual HTTP checks also passed for all **11 independent-Python-reference overview
fixtures**, **834 IDs across 14 page requests**, and **nine sampled details**, with
the same bounded pagination coverage as the earlier run. Overall stayed 97,652;
2024-2026 CARROTS 149; all-year CARROTS 241; literal plus 1,811; underscore 2;
calendar year 2026 24. Empty, Unicode-casefold and trailing-space fixtures retained
their original behavior. Wrong request release IDs returned 409.

This did not rerun the original CLI/raw-page oracle, exhaustive 1,530-page parity
suite, frontend build or full browser suite. Those earlier results remain historical.

## Resource and HTTP Results

The serving test used **0.1 CPU**, **512,000,000 bytes RAM**, no swap, UID/GID 10001,
read-only root, dropped capabilities and no-new-privileges. Observed controls were
`cpu.max = 10000 100000` and `memory.max = 512000000`; throttling was active.

| Scenario | Successful / total | p95 | Maximum |
| --- | --- | --- | --- |
| Warm default, ten five-client waves | 50 / 50 | **76.84 ms** | 82.51 ms |
| Repeated uncached CARROTS, two waves | 10 / 10 | 8,262.16 ms | 8,262.16 ms |
| Mixed uncached selections, two waves | 10 / 10 | 4,803.17 ms | 4,803.17 ms |
| Defaults mixed with filtered work, two waves | 10 / 10 | 2,090.71 ms | 2,090.71 ms |
| Defaults arriving during five SQL requests | 5 / 5 | 484.67 ms | 484.67 ms |
| Those five background SQL requests | 5 / 5 | 5,996.88 ms | 5,996.88 ms |

The revised **default p95 <10 seconds** gate passes locally. Filtered samples are
small and have no newly imposed universal latency gate. For ten samples,
nearest-rank p95 equals maximum. Timings start before executor submission and end
after the complete host-loopback HTTP body, including scheduling/dispatch wait.
These closed-loop waves are not growing queues, internet/browser latency or actual
provider resources. No filtered cache/evictions or application pending queue exists.

Filtered observations were slower than the earlier local image run. These are not
a controlled before/after experiment: runtime/base/cache state, host scheduling and
the inspection harness differ. No cause or speedup is established. The 30-second
SQL budget and five-job admission policy were not changed to obtain successes.

The ten-request overload batch returned five successes and five expected HTTP 503
busy responses, all retained. Server resident high-water memory was **103,292 KiB /
100.87 MiB**; container-accounted peak was **113,385,472 bytes / 108.13 MiB**. The
latter includes inspection work and cache charged to that container, not the whole
WSL VM or a prediction of all cache/host conditions. Do not interpret its lower
value versus the earlier run as a controlled memory improvement. No memory-limit
or OOM events were recorded.

Initial Docker-start-through-readiness observation was **13.03 seconds**. Restart
readiness polling was **11.85 seconds**, starting after the Docker start command
returned; the timers differ and neither measures provider idle wake. Same-image
restart retained the correct default and release. Graceful final exit was 0, and
the harness removed its own container. Local images/Docker Desktop remain available.

## Evidence and Remaining Boundaries

Ignored evidence: `generated/deployment/refresh-before.json`,
`runtime-refresh-regressions/regression-results.json`, and
`runtime-refresh-http-20261021/results.json`/`container.log`, all under
`generated/deployment`. Test wheels and all databases/archives remain ignored.

This addresses the reviewed stale-runtime/build-tool maintenance items, not a
universal security clearance. The Bookworm trackers still list open OpenSSL/SQLite
issues; reaching a current distro package does not make all native-library
advisories disappear. No exhaustive OS/native advisory mapping or independent
full-image CVE scanner was run. The application still uses the checked immutable
database and fixed parameterized SQL, accepts no arbitrary SQL/database/archive
uploads, and uses intended provider TLS rather than runtime TLS in its public
candidate configuration. Do not silently migrate distributions or claim all
listed advisories are proven exploitable or proven irrelevant.
[OpenSSL tracker](https://security-tracker.debian.org/tracker/source-package/openssl),
[SQLite tracker](https://security-tracker.debian.org/tracker/source-package/sqlite3).

Review this local result before any public step. Publication/service creation still
requires its separate approval and account-specific $0 checks. Real origins/TLS,
version pairing, fallback, hosted p95/memory, genuine idle wake, rollback and later
portfolio integration remain unverified. Reproducibility is the checked local
image/working tree, not a CI/source-only supply-chain guarantee. Upstream test
publication and original builder-permission questions remain unresolved.
Completion/teaching/resume/Flex reminders remain pending.
