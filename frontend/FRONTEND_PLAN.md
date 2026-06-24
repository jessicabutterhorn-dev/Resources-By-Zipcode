## Front-End Spec — Static HTML + sql.js, Print-Friendly

**Goal:** A zero-backend, single-folder site a member (or a navigator on their behalf) can open, enter a ZIP, and get a printable sheet: "Here's what you're losing on 1/1/2027, and here are verified local providers that can help." Works offline once loaded; deployable on any static host.

### Stack (locked)
- **sql.js** (SQLite compiled to WebAssembly) loads `directory.sqlite` entirely in the browser. No server, no API, no PHI risk (nothing leaves the device).
- Vanilla HTML/CSS/JS (no framework) to keep the bundle small, auditable, and durable across quarterly rebuilds.
- The DB ships as a static asset built by the pipeline (`pipeline/build_frontend`).

### Data flow
1. Page load: fetch `directory.sqlite` (and the sql.js `.wasm`) as static assets; instantiate an in-browser DB.
2. **ZIP input** -> query `v_zip_zone` to resolve ZIP -> county(ies) + zone. (Kansas City ZIPs return multiple counties via the HUD crosswalk; show all, ordered by `is_primary` then `res_ratio`.)
3. **Losses panel** (optional): query `v_losses_by_zip` filtered to the member's county to show "benefits ending 1/1/2027" and their `resource_bucket` mapping.
4. **Resources panel:** query `v_resource_by_zip` for the resolved zone/county, grouped by `resource_bucket` (food, utility, rent, pet_food, gas_transport, prescription, housing, navigation).
5. Each card renders org name, public phone, address, hours, eligibility, plus a **verification footer**: `confidence` badge + `source_url` + `date_checked`. Low-confidence records are visually flagged ("verify before relying on").

### Print-friendly CSS
- A dedicated `@media print` stylesheet: hide search controls, expand all result cards, use high-contrast black-on-white, 11pt serif, page-break-avoid inside cards, repeat a header ("KS/MO Benefit-Loss Resource Sheet — printed {date}").
- A "Print this list" button calls `window.print()`. The printout always includes the credits/attribution line and per-record source + date so a paper copy stays self-verifying.
- Phone numbers and addresses render large; URLs print as full text (not just links).

### Accessibility / audience
- Large default font, keyboard navigable, semantic HTML, ARIA labels — audience skews older + low-vision. No reliance on JS-only interactions for core reading.
- Bilingual-ready: keep all UI strings in one JS object for easy translation pass later.

### Hosting options (deliberate, governance-gated)
- **GitHub Pages** (simplest) — but resolve the Aetna IP/governance sign-off first (compliance §1D) before any public repo. Keep personal vs enterprise accounts strictly separated.
- **Netlify / Cloudflare Pages** — static, free tier, custom domain.
- **Offline / USB / intranet** — because it's fully static, the folder runs from `file://` or an internal share for navigators; good fallback if public release is blocked by governance.
- Whatever host: serve over HTTPS, set long cache on `.wasm`, short cache on `directory.sqlite` so quarterly refreshes propagate.

### Credits/attribution page (required)
- Render the `source` table's `attribution_text` for every source with `attribution_required = 1` (USDA SNAP CC BY, HSDS spec CC BY-SA, etc.). HIPAA-not-applicable rationale linked from footer.

### Minimal `index.html` sketch
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>KS/MO Benefit-Loss Resource Finder</title>
  <link rel="stylesheet" href="styles.css"/>
  <link rel="stylesheet" href="print.css" media="print"/>
</head>
<body>
  <header><h1>Find local help after your 1/1/2027 benefit change</h1></header>
  <main>
    <form id="zip-form" aria-label="ZIP lookup">
      <label for="zip">Enter your ZIP code</label>
      <input id="zip" inputmode="numeric" pattern="\d{5}" maxlength="5" required/>
      <button type="submit">Find resources</button>
    </form>
    <section id="losses" aria-live="polite"><!-- benefits ending --></section>
    <section id="results" aria-live="polite"><!-- grouped resource cards --></section>
    <button id="print-btn" type="button">Print this list</button>
  </main>
  <footer>
    <a href="credits.html">Sources &amp; attribution</a> ·
    <a href="hipaa.html">Why this contains no personal data</a>
  </footer>
  <script src="sql-wasm.js"></script>
  <script>
    // Pseudocode flow:
    // const SQL = await initSqlJs({locateFile: f => f});
    // const buf = await (await fetch('directory.sqlite')).arrayBuffer();
    // const db  = new SQL.Database(new Uint8Array(buf));
    // on submit: resolve ZIP via v_zip_zone, then render v_losses_by_zip + v_resource_by_zip.
    // Every card MUST print confidence + source_url + date_checked.
  </script>
</body>
</html>
```

### Folder layout (`frontend/`)
```
frontend/
  index.html
  credits.html          # generated from source table
  hipaa.html            # HIPAA-not-applicable rationale (from docs/)
  styles.css
  print.css
  app.js
  sql-wasm.js / sql-wasm.wasm
  directory.sqlite      # built by pipeline, copied in at build_frontend stage
```
