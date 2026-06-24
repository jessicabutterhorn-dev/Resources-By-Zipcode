## Front-End Spec — Static, Print-Friendly Resource Finder

**Goal:** A zero-backend, single-folder site a member (or a navigator on their
behalf) can open, enter a ZIP, and get a printable sheet of verified local
providers that can help (food, utility, rent, pet food, gas/transport,
prescription, housing). Works offline; deployable on any static host.

### Stack (as built)
- Vanilla HTML/CSS/JS, no framework — small, auditable, durable across rebuilds.
- The page reads `data.js`, a static JSON export generated from the SQLite
  source of truth by `pipeline/build_frontend.py` (the `build_frontend` stage).
  This keeps the page fully self-contained: it runs by double-clicking
  `index.html` (`file://`) with no server and no internet.
- **Why not sql.js:** loading a `.sqlite` file in-browser needs `fetch()` +
  WebAssembly, which is blocked from `file://` (CORS) — it would force a local
  server. The static JSON export gives the same result with zero setup. SQLite
  remains the source of truth; `build_frontend.py` is the bridge. (If a hosted
  build is ever wanted, sql.js against `directory.sqlite` is a drop-in upgrade.)

### Data flow
1. Page load: `data.js` sets `window.RESOURCE_DATA` (ZIP -> county/zone + resources).
2. **ZIP input** -> look up the ZIP -> show county, state, collection zone.
3. **Resources panel:** resource cards grouped by `resource_bucket` (food,
   utility, rent, pet_food, gas_transport, prescription, housing, navigation).
4. Each card renders org name, public phone, address, hours, eligibility, how to
   apply, cost, plus a **verification footer**: `confidence` badge + `source_url`
   + `date_checked`. Unverified records are visually flagged.

### Print-friendly CSS
- `@media print`: hides search controls + sample banner, expands all cards,
  high-contrast black-on-white, page-break-avoid inside cards, prints full source
  URLs + date so a paper copy stays self-verifying.
- A "Print" button calls `window.print()`.

### Accessibility / audience
- Large default font, keyboard navigable, semantic HTML — audience skews older /
  low-vision. Keep UI strings together for an easy bilingual pass later.

### Hosting options (deliberate, governance-gated)
- **Offline / USB / intranet** — fully static, runs from `file://` or an internal
  share. Best fallback if public release is blocked by governance.
- **GitHub Pages / Netlify / Cloudflare Pages** — only after the Aetna IP/governance
  sign-off (compliance §1D). Keep personal vs enterprise accounts separated.

### Credits/attribution page (required for production)
- Render the `source` table's `attribution_text` for every source with
  `attribution_required = 1` (USDA SNAP CC BY, HSDS spec CC BY-SA, etc.).

### Folder layout (`frontend/`)
```
frontend/
  index.html        # ZIP search + printable resource cards (as built)
  data.js           # generated from SQLite by pipeline/build_frontend.py
  FRONTEND_PLAN.md  # this spec
```
