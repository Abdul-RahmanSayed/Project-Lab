# Slice 5A: $0 Hosting Review and Deployment Proposal

Reviewed October 20, 2026. **This is the authorized research/proposal phase, not a deployment result.** No account, service, release asset, container image, Pages site or portfolio change was created or published. No implementation code, database, source pin, commit or push was changed by this review.

Subsequent status: Abdul approved **local deployment preparation only**, explicitly
excluding accounts, provisioning, publication, visibility/portfolio changes, commits
and pushes. That implementation and its remaining Linux/hosted checks are recorded
in [Slice 5B results](SLICE_5_LOCAL_PREPARATION_RESULTS.md). Proposed future external
actions below remain gated, not completed or authorized by the local tests.

October 21 update: the repository is now confirmed public; Abdul reports a Hobby
Render account with its payment method removed and has installed Docker/WSL2.
Local Linux checks subsequently passed. See [the follow-up](SLICE_5_LINUX_RESULTS.md)
for current evidence and the remaining public-runtime/hosted acceptance boundaries.
The earlier account/access observations below retain their original review date.

## Recommendation in Plain Language

Keep the existing portfolio as the entry point. Put the Explorer's browser files on GitHub Pages and run its existing Python API on one Render Free web service. Package the checked SQLite snapshot with the API so it does not need a separate paid database or disk. A sleeping API does not prevent the static page from showing its clearly labeled saved overview.

Use a Docker container: a packaged runtime containing the application and its checked files. Have Render build it from a reviewed Project Lab commit; do not introduce another public container registry or deployment framework for this MVP. This preserves the intended React/TypeScript/D3, modular FastAPI and read-only SQLite architecture.

**Conditional go:** published provider limits look suitable for a hobby demo. Account eligibility, Linux compatibility and hosted acceptance are not established yet. If Render requires a payment method or paid plan, stop and review; do not enter billing information or assume a spending limit covers every charge.

## Account and Repository Facts

- Abdul confirmed he does not have a Render account. Its actual signup/verification flow has not been attempted. The provider's documentation describes no-payment-method suspension behavior, but that does not guarantee every new account can provision without verification or a card.
- The local origin is `https://github.com/Abdul-RahmanSayed/Project-Lab.git`; branch `development`, inspected checkpoint `0006a3d` (frontend MVP). Public browsing and the connected GitHub metadata tool both returned 404. That does not prove the repository is private: access permissions, an unpushed/nonexistent repository or a different remote could also explain it.
- Abdul is willing to make Project Lab public if that simplifies hosting. No visibility change was performed. Confirm the actual repository/access first, and review tracked content and history for secrets/private material before publication. A tracked-filename check found no SQLite/database, generated build, `.env`, private-key or credential-named files; this is **not** a content/history secret audit.
- GitHub Pages is available from public repositories on GitHub Free. Public source is therefore the preferred path here, not a requirement imposed by Render. If Abdul chooses to keep source private, reconsider the frontend host rather than upgrading GitHub or changing visibility silently. [GitHub Pages eligibility and limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits), [Render Git-provider access](https://render.com/docs/git-provider).

## Current Provider Findings

| Component / option | Verified published terms | Decision |
| --- | --- | --- |
| Render workspace | Hobby has no monthly plan fee; usage can still be billed. | Use Hobby only, with no paid resources. [Plan features](https://render.com/docs/platform-features-by-plan) |
| Render API compute | Free web service: 0.1 CPU, 512 MB RAM. | Candidate, subject to actual hosted measurements. [Compute plans](https://render.com/docs/compute-plans) |
| Render lifecycle | Sleeps after 15 idle minutes; wake is approximately one minute. Filesystem changes disappear on restart/redeploy/sleep. | Bake the snapshot into the image; no runtime preparation. [Free services](https://render.com/docs/free) |
| Render usage | 750 running hours/workspace/month; exhausted hours suspend free services. Free rollback covers the two most recent previous deploys. | One API, no keep-awake traffic, retain independent rollback files. [Free services](https://render.com/docs/free) |
| Render transfer | Hobby includes 5 GB outbound/month, shared by workspace services. Above the allowance, a payment method can be billed; without one, services are stopped until the next month. | Prefer no payment method and suspension over spending. [Bandwidth](https://render.com/docs/outbound-bandwidth) |
| Render builds | Hobby includes 500 Starter pipeline minutes/month. Build disk limit is 16 GB. Builds stop at the allowance if no payment method or the pipeline spend limit is reached. | Manual, bounded releases; no automatic preview services. A pipeline limit is not a universal account spending cap. [Build pipeline](https://render.com/docs/build-pipeline) |
| GitHub Pages | Published site limit 1 GB; soft transfer limit 100 GB/month. | Static frontend only, not the API/database. [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) |
| GitHub Actions / Releases | Standard public-repository runners are free; larger runners are billed and storage has separate allowances. Release assets must each be under 2 GiB. | Use standard runners only if needed; short-lived test artifacts, no paid storage assumption. Store the snapshot as a reviewed release attachment, not a Git blob. [Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions), [Release assets](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) |
| Hugging Face Spaces | New Docker/Gradio compute Spaces require a paid plan despite CPU Basic having no hourly charge. | Not a new-account $0 FastAPI fallback. [Spaces eligibility](https://huggingface.co/docs/hub/spaces-overview) |
| Koyeb | Current signup FAQ describes a card requirement, $29 authorization hold and an initial prorated selected-plan charge. | Do not use this signup path under the $0 constraint. [Pricing FAQ](https://www.koyeb.com/docs/faqs/pricing) |

A Render static site is a fallback frontend host if Pages eligibility is unsuitable; it would share Render's bandwidth/build allowance with the API. It does not remove Render account verification. No fallback service was provisioned. [Static sites](https://render.com/docs/static-sites).

This was a focused documentation review, not an exhaustive provider search or an account-specific eligibility approval. Recheck terms at provisioning; free tiers can change. Use provider-supplied HTTPS hostnames, with no purchased domain, add-ons, paid disk, external database, autoscaling or scheduled pings.

## Existing Resource Fit

- Checked database: **62,152,704 bytes / 59.27 MiB**. Its SHA-256 was rechecked during this review and is still `bdfd771ede151a2784a83ff1e9ba1faad727491cce2bddf73a0499521b4d475f`.
- The five release files total **62,354,679 bytes**, before archive/container overhead. Render's published build-disk limit leaves ample room for these files, but the built image/runtime footprint remains unmeasured. No fixed Free runtime-disk capacity is assumed.
- Historical Slice 3: **114.56 MiB** peak server resident memory; default five-client p95 **302.46 ms**, 50/50 successful requests under the recorded desktop constraints. Those are not fresh Linux/container measurements. The local 512 MiB commit cap is not identical to the provider's published 512 MB allocation or total container memory.
- Frontend: about **486 kB JS + 16 kB CSS + 89 kB fonts**, uncompressed, plus the small HTML entry. The browser does not download the 62 MB database. Published static-site limits look suitable; this is not a visitor-capacity or public-abuse guarantee.

No parity suite, CPU/memory profile, browser suite or hosted load test was rerun for this documentation phase. Existing results remain in [Slice 3](SLICE_3_RESULTS.md) and [Slice 4](SLICE_4_RESULTS.md).

## Bounded Implementation After Approval

### 1. Package the Existing Checked Release

Use release `fda-release-sha256:18446003726ef6cb89bbb5cd07a265e8cf9fb3e4585fe5774ed4f6fd18454194`, not a new snapshot. Create an archive containing only `release.json`, `fda.sqlite3`, `metadata.json`, `page-inventory.json` and `saved-overview.json`; pin the archive checksum and expected release ID in a small deployment manifest.

Publish the archive as an explicitly approved GitHub Release attachment. A release attachment is a downloadable build artifact, not a file committed into Git history. Publishing it exposes the retained public dataset in bulk and still needs approval. Do not use Git LFS, a moving `latest` URL, raw FDA pages or a visitor-triggered downloader. The build must verify the archive and all release hashes before using it; reject unsafe archive paths/links and extra files.

Bake those checked bytes into a Linux image with readable, non-writable release-file permissions for the serving user. Do not copy the Windows directory's access restrictions. This does not repair or repin the original Windows builder. Keep preparation offline and preserve raw substring/casefold, normalization, age and counting policies.

Pin the reviewed Python 3.14 runtime/base image and check Linux dependency availability, query-code byte identity, SQLite compatibility and representative parity before deployment. Do not silently rewrite locked code or rebuild the data to make startup pass. The current snapshot comes from the reviewed Windows/local-working-tree process; shipping it in a container does not establish a public-source rebuild or supply-chain guarantee. The upstream core/test publication questions remain separate.

### 2. Make the Existing API Reachable

Add only deployment wiring: one process on `0.0.0.0:$PORT`, using the existing app factory, exact release settings, five SQL jobs, no application pending queue and 30-second SQL budget. Preserve the local loopback runner. Keep request-target/response bounds and query-safe logging.

Use `/readyz` as the provider health check, not just `/healthz`, so an unreadable or mismatched snapshot cannot be accepted as ready. Render requires public web services to listen on `0.0.0.0`; its HTTP health check must succeed within five seconds. [Web-service binding](https://render.com/docs/web-services), [Health checks](https://render.com/docs/health-checks).

Let Render build the Dockerfile from an explicitly reviewed commit with automatic deploys disabled. Docker builds are supported directly, without a separately published registry image. [Docker deployment](https://render.com/docs/docker), [Manual deploys](https://render.com/docs/deploys).

### 3. Connect the Static Frontend

Proposed Pages URL, not an existing deployment: `https://abdul-rahmansayed.github.io/Project-Lab/#/fda`. Keep hash navigation and test assets/direct links under `/Project-Lab/`.

The current frontend calls relative `/api/...` paths and works only because Vite proxies them locally. Add a trusted build-time HTTPS API origin for production, preserving the local proxy path. Never take an API URL from a visitor's search/link, and put no secret in the browser build.

Configure the API's existing CORS allowlist for `https://abdul-rahmansayed.github.io`, without a repository path. An origin means scheme + hostname + port, not `/Project-Lab/`. The portfolio and its project sites share that origin; CORS is not authentication or an abuse/spending shield. No credentialed requests or wildcard origin.

Keep the saved payload tied to its exact release/default filters. Deploy frontend and API as a recorded compatible pair. A wrong release must fail visibly rather than supply a different dataset or relabel the saved default.

### 4. Preserve Honest Wake-Up Behavior

Keep the saved overview visible immediately and label all API results as saved-snapshot data. The existing metadata flow can finish its three eight-second attempts, including delays, in about 30 seconds; that can end before Render's documented approximate minute-long wake. Initially retain bounded attempts plus manual Retry rather than adding a polling/keep-awake system. Test and disclose that a cold visit may need Retry after the service wakes.

Do not extend the SQL deadline or call sleeping/quota errors zero results. Custom selections must never receive the unrelated default. If actual hosted evidence shows a small bounded metadata-only retry adjustment is needed, review that change against the cold-start test, not a new general retry/cache framework.

### 5. Add the Portfolio Link Last

Only after the hosted demo passes acceptance, propose the narrow edit to the existing FDA project entry in `artifacts/portfolio/src/components/ProjectsSection.tsx`: add the Live Demo link and accurately distinguish the Explorer extension from the original take-home pipeline. Preserve existing attribution and historical claims; no resume edits.

Do not import the Explorer into the portfolio bundle, embed it, prefetch its API, load the database, or wake Render merely to display the portfolio project card. Keep the existing portfolio build/deploy ownership and production-review process. No portfolio edits are authorized by this research result alone.

## Hosted Acceptance and Rollback

These checks are planned, **not passed**:

| Check | Evidence required |
| --- | --- |
| Account/cost | Confirm eligible no-fee workspace + Free service, no payment method/paid resources, actual quotas and remaining usage. Stop at any billing requirement. |
| Build/readiness | Linux startup and checked database/query hashes match; `/readyz` succeeds; wrong ID/missing/unreadable release fails closed in pre-host tests. Record actual artifact sizes and runtime versions. |
| Real HTTPS/browser origin | Pages assets and hash links load at the actual project URL; the actual frontend origin can query the API. Check allowed/disallowed Origin headers and application errors. A blocked origin is not claimed to block nonbrowser callers. |
| Data compatibility | Default 97,652 reports; 2024-2026 CARROTS 149/123 valid/26 missing, annual 122/27/0; literal punctuation, empty selection, all chart/table values, complete deterministic pagination and retained details match the reviewed reference. Verify release/default identity and explicit mismatch rejection. |
| Warm latency/resources | Ten waves of five successful default HTTPS requests; record nearest-rank p95 <10 seconds, maximum and failures separately. Measure full-body network request latency, not just server time. Record repeated/mixed uncached samples including wait and actual available memory measurements. No new hard threshold for every filter; distinguish sampled provider memory from measured process peak. |
| Genuine idle wake | With tests/tabs closed and no pings, let the service actually idle beyond 15 minutes. Confirm sleep/wake evidence, saved-first display, bounded connection attempts and recovery after Retry. Cold wake is reported separately from the warm p95 gate. |
| Failure fallback | Check real unreachable/busy responses where safely reproducible; use bounded fixtures for quota/proxy/version failures, without deliberately exhausting a monthly quota or claiming a simulated quota is a real provider event. Previous values retain their original labels. |
| Rollback | Retain current and previous source references, release archive, frontend assets/bundle and configuration record. Rehearse a harmless same-data application deploy and restoration; verify readiness, hashes, overview and filters afterward. No new snapshot/policy is needed for this drill. Restore a compatible frontend/API pair, not database contents in place. |
| Portfolio | After approval and integration, the live card opens the verified demo; portfolio home causes no FDA-data/API requests. Smoke-test the existing portfolio. |

Render Free retains only two previous deploys; do not rely on indefinite provider history. Preserve reviewed source/artifacts so a rebuild remains possible, and test restoration rather than merely documenting a button. Environment/origin/release settings must accompany the rollback record. [Free retention](https://render.com/docs/free), [Rollback behavior](https://render.com/docs/rollbacks).

The existing admission controls bound ordinary work, not arbitrary sustained abuse. No public-load capacity, instant cancellation or universal $0-forever guarantee is claimed. If quotas or resource limits fail, keep an honest saved-only fallback and review rather than upgrading automatically.

## Review Decision Needed

Approve or revise this **GitHub Pages + one Render Free API + checksum-pinned GitHub Release archive** setup before implementation/provisioning/publication. Repository accessibility/publication readiness and Render's real account verification are still open checks. Abdul should handle account signup and any third-party terms personally; stop if a card or charge is required. Never paste credentials into chat.

Approval should distinguish local deployment-file implementation from external account/resource/artifact publication and the later portfolio edit. No commit, push, repository visibility change or production-branch update is inferred. The original baseline plan remains unchanged; this proposal narrows its Slice 5 to the existing MVP, without Slice 6 filters/parallel coordinates or another project.

FDA adverse-event reports are not unique people, causation, incidence, relative risk or product-safety conclusions. The completion/teaching/resume/Flex reminder remains pending until the agreed feature is genuinely complete and verified end to end.
