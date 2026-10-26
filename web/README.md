# FDA Explorer Local Frontend

Use Node 24.13+ (24.x), the committed npm lockfile, and the checked local backend on port 8765.

## Run and Verify

From `web/` in PowerShell:

```powershell
npm.cmd ci
npm.cmd run build
npm.cmd run preview
```

Open `http://127.0.0.1:4173/`. `npm.cmd run dev` provides hot reload on port 5173. Both bind to loopback only. The Vite proxy forwards API requests to `http://127.0.0.1:8765`; set the trusted process environment variable `FDA_API_TARGET` before starting Vite if the backend uses another local port. A frontend URL never chooses arbitrary backend files or an API target.

```powershell
npm.cmd test
npm.cmd run test:e2e
```

The browser tests require the preview and backend already running. They use installed Chrome through Playwright's `chrome` channel, not downloaded browsers or accounts. If needed, set `FRONTEND_URL` to another local preview port. Results, traces and screenshots go under the ignored root `generated/frontend/` directory. Tests do not start deployment or modify the FDA checkout.

## Checked Saved Artifacts

`src/generated/` contains public metadata, the labeled default overview, OpenAPI, generated TypeScript and a bundle hash inventory. These small public artifacts are intentionally source-controlled; database files, raw pages, node_modules, built output and test evidence are not. The API environment exports them only after its normal full release validation:

```powershell
# Run from the Project Lab root, using the selected reviewed release values.
.\.venv-api\Scripts\python.exe -B data-build\frontend_bundle.py --release-directory $releaseDir --release-id $releaseId
npm.cmd --prefix web run build
```

`build` checks the bundle, regenerates types, typechecks and compiles. The export and narrow Git attributes pin LF endings for byte-hashed generated JSON; existing backend files are unaffected. No automatic snapshot refresh or database preparation occurs. A new release/policy/schema still needs the separate reviewed pin/rebuild process. A different API release is rejected, not silently substituted; rebuild the frontend's saved artifacts against the reviewed matching release. Browser response validation uses the generated OpenAPI schemas, then checks release, dataset/policy, acquisition time, exact applied filters and report/page identity.

## Code and Behavior

- `Header.tsx` / `theme.ts`: same-tab return to the portfolio and light/dark appearance on every Explorer tab and the render-error fallback. The existing same-origin `theme` preference is shared with the portfolio; controls and other tabs synchronize. Storage failures preserve a working in-page control. Theme state is separate from filter URLs and data requests. See the [local follow-up checks](#navigation-and-theme-checks).
- `App.tsx`: one committed selection, separate draft fields, Apply, hash navigation, metadata connection flow and the displayed-result boundary. Source/methods describes the actual snapshot and limitations.
- `selection.ts`: strict URL round-tripping, raw-search preservation, UTF-8 identifier ordering, and at most 100 previous page bookmarks. It stores no result pages or personal defaults.
- `api.ts` / `contracts.ts`: bounded response reads and deadlines, generated-schema validation, exact context checks, error handling and URLSearchParams transport. Metadata gets at most three connection attempts, then manual retry; SQL queries do not auto-retry.
- `useRequest.ts`: abort on supersession/unmount plus a generation guard against noncooperative late loaders. It retains at most one previous response for truthful stale display, not a filter-keyed cache.
- `charts.tsx`: five views using D3 scales with React-owned SVG/DOM. The server's annual counts, 126 age bins and canonical rankings are rendered directly; no second normalization or aggregation policy. Accessible tables expose exact values; mean display rounding is not an analytical recalculation.
- `Reports.tsx`: server-side pages and on-demand retained-field detail. Changing selection/page size resets paging; Next/Previous/First never cache rows. Native dialogs support Escape, close, focus containment and return to the report opener.
- `styles.css` / `tokens.css` / `fonts.css`: responsive operational layout matching the portfolio's dark/light palettes and typography, fixed chart heights, container-based geometry, full wrapping, contrasting semantic accents and reduced-motion support. Pinned Inter/JetBrains Mono normal Latin variable faces are self-hosted, with system fallbacks for other Unicode glyphs. Their OFL notices ship in `public/fonts/LICENSES.txt`. No font CDN, decorative imagery or generic dashboard shell framework.

The saved default is eligible only for its exact year/product selection and release. An initial custom URL displays no default answer while connecting. A prior result can remain during a new query only with its actual original filters and a previous-result label. Invalid links have an explicit repair action. All data remains a saved snapshot even when the API is ready; January 1, 2026 is marked as a partial year.

The API's five SQL jobs/no pending queue and 30-second budget remain unchanged. Frontend request cancellation does not promise instant termination of every proxy/filesystem/native operation. Local Vite proxy behavior is not production hosting, cross-origin/CORS, sleeping-service recovery or an actual provider quota test.

## Local Deployment Preparation

After the separate Slice 5B approval, `VITE_FDA_API_ORIGIN` selects a trusted plain
HTTPS API origin at build time; it is not a secret or visitor-controlled setting.
With no origin, the normal build keeps its existing local proxy behavior.
`npm.cmd run build:deployment` requires that origin and writes separately under
`generated/deployment/site/Project-Lab`, retaining relative assets and hash routes.
Requests explicitly omit credentials; response/filter/release checks are unchanged.

`npm.cmd run test:deployment` uses the prepared local wheel/release and short-lived
self-signed certificate described in the [deployment guide](../deployment/README.md).
It owns separate loopback HTTPS servers and tests actual cross-origin requests,
process outages and Retry recovery. Its dedicated config alone bypasses the local
test certificate's trust check; that is not suitable for public hosted verification.
No deployment or portfolio integration is claimed by these checks.

FDA report mentions are not unique people, causation, incidence, relative risk or product-safety conclusions. No full raw report JSON, original age/unit strings or raw reaction strings are invented for details.

## Navigation and Theme Checks

October 26, 2026 local follow-up; not yet published. Both frontends use the existing
same-origin `localStorage` key `theme` (`dark` or `light`, default dark), apply the
preference before React renders, and synchronize controls, other tabs and restored
pages. Other origins have separate browser storage. Blocked storage leaves an
in-page control working without promising persistence between documents.

- Explorer saved-bundle verification, type generation, typecheck and build passed,
  along with 20 existing frontend tests and five focused browser regressions in
  `e2e/theme.spec.ts`. The focused suite uses saved API fixtures and needs a local
  preview; it does not require a running API.
- Portfolio typecheck and build passed using its installed tools. Its package
  runner attempted an unnecessary reinstall and stopped before removal; manifests,
  dependencies and lockfiles were not changed. Vite emitted a source-map warning
  for untouched `ui/tooltip.tsx`, then exited successfully.
- Eight combined local flow checks passed: shared appearance through the actual
  Live Demo link, cross-tab updates without new data requests, keyboard and pointer
  return-home navigation, Back, 320/390px layouts without page overflow, and the
  portfolio's Home/client-side not-found controls. No browser exceptions occurred.
- Explorer text/notices met the checked 4.5:1 contrast threshold and chart marks /
  control borders met 3:1 in both themes. Exact-value tables remain available.
  This is focused accessibility evidence, not full certification.
- The bounded homepage/project-card observation attempted zero FDA requests.
  Returning home and changing appearance triggered no additional FDA request.

Evidence stays ignored under `generated/frontend/qol/`: `theme-results.json`,
`cross-site-results.json` and screenshots. The combined check serves local
production builds through intercepted same-origin URLs, supplies checked saved
API fixtures and blocks outside requests. An initial pointer-driven popup attempt
timed out; the completed flow opened Live Demo by keyboard and checked the new
return link by keyboard and pointer. No hosted service was contacted or woken.
The data release, policies, backend, origins and deployment wiring are unchanged;
no new hosted performance, memory, wake-up or rollback result is claimed.
