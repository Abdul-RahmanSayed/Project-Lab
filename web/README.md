# FDA Explorer Local Frontend

Slice 4 consumes the [implemented API](../docs/API_CONTRACT_IMPLEMENTED.md); it does not change FDA analysis policies or implement deployment. Use Node 24.13+ (24.x), the committed npm lockfile, and the checked local backend on port 8765.

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

The browser tests require the preview and backend already running. They use installed Chrome through Playwright's `chrome` channel, not downloaded browsers or accounts. If needed, set `FRONTEND_URL` to another local preview port. Results, traces and screenshots go under the ignored root `generated/frontend/` directory. Tests do not start deployment or modify the FDA checkout. See [Slice 4 results](../docs/SLICE_4_RESULTS.md) for what was actually verified.

## Checked Saved Artifacts

`src/generated/` contains public metadata, the labeled default overview, OpenAPI, generated TypeScript and a bundle hash inventory. These small public artifacts are intentionally source-controlled; database files, raw pages, node_modules, built output and test evidence are not. The API environment exports them only after its normal full release validation:

```powershell
# Run from the Project Lab root, using the selected reviewed release values.
.\.venv-api\Scripts\python.exe -B data-build\frontend_bundle.py --release-directory $releaseDir --release-id $releaseId
npm.cmd --prefix web run build
```

`build` checks the bundle, regenerates types, typechecks and compiles. The export and narrow Git attributes pin LF endings for byte-hashed generated JSON; existing backend files are unaffected. No automatic snapshot refresh or database preparation occurs. A new release/policy/schema still needs the separate reviewed pin/rebuild process. A different API release is rejected, not silently substituted; rebuild the frontend's saved artifacts against the reviewed matching release. Browser response validation uses the generated OpenAPI schemas, then checks release, dataset/policy, acquisition time, exact applied filters and report/page identity.

## Code and Behavior

- `App.tsx`: one committed selection, separate draft fields, Apply, hash navigation, metadata connection flow and the displayed-result boundary. Source/methods describes the actual snapshot and limitations.
- `selection.ts`: strict URL round-tripping, raw-search preservation, UTF-8 identifier ordering, and at most 100 previous page bookmarks. It stores no result pages or personal defaults.
- `api.ts` / `contracts.ts`: bounded response reads and deadlines, generated-schema validation, exact context checks, error handling and URLSearchParams transport. Metadata gets at most three connection attempts, then manual retry; SQL queries do not auto-retry.
- `useRequest.ts`: abort on supersession/unmount plus a generation guard against noncooperative late loaders. It retains at most one previous response for truthful stale display, not a filter-keyed cache.
- `charts.tsx`: five views using D3 scales with React-owned SVG/DOM. The server's annual counts, 126 age bins and canonical rankings are rendered directly; no second normalization or aggregation policy. Accessible tables expose exact values; mean display rounding is not an analytical recalculation.
- `Reports.tsx`: server-side pages and on-demand retained-field detail. Changing selection/page size resets paging; Next/Previous/First never cache rows. Native dialogs support Escape, close, focus containment and return to the report opener.
- `styles.css` / `tokens.css` / `fonts.css`: responsive operational layout matching the production portfolio's default dark palette and typography, fixed chart heights, container-based geometry, full wrapping, contrasting semantic accents and reduced-motion support. Pinned Inter/JetBrains Mono normal Latin variable faces are self-hosted, with system fallbacks for other Unicode glyphs. Their OFL notices ship in `public/fonts/LICENSES.txt`. No font CDN, decorative imagery or generic dashboard shell framework.

The saved default is eligible only for its exact year/product selection and release. An initial custom URL displays no default answer while connecting. A prior result can remain during a new query only with its actual original filters and a previous-result label. Invalid links have an explicit repair action. All data remains a saved snapshot even when the API is ready; January 1, 2026 is marked as a partial year.

The API's five SQL jobs/no pending queue and 30-second budget remain unchanged. Frontend request cancellation does not promise instant termination of every proxy/filesystem/native operation. Local Vite proxy behavior is not production hosting, cross-origin/CORS, sleeping-service recovery or an actual provider quota test.

FDA report mentions are not unique people, causation, incidence, relative risk or product-safety conclusions. No full raw report JSON, original age/unit strings or raw reaction strings are invented for details.
