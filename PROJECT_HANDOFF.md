# KS + MO Community Resource Finder — Project Handoff

A pick-up-and-continue guide to the whole project: what it is, how to run it,
how it's built, the rules that keep it trustworthy, and what's left.

> **⚠ DIRECTION UPDATE (2026-06-26):** Target deployment is shifting from a
> public hosted website to an **internal Aetna build (Snowflake + Streamlit on
> the intranet)**, used by staff as a **single-ZIP print generator**. This
> resolves the IP/governance gate and unlocks the gated feeds. See **§11** for
> the full decision record — read it before acting on §9's "go public" plan.

---

## 1. What this is

A **ZIP-searchable, printable directory of public community resources across
Kansas and Missouri** — built so Medicare members who lose their SSBCI / flex /
grocery-card benefits (CMS-4208-F, effective **1/1/2027**) can find local
replacements: food, hygiene, dental, vision, prescription, rent, pet food,
utility, housing, transportation, and navigation help.

- **Audience:** low-income, often older, often **no computer** → every listing
  has a phone; the page prints cleanly.
- **Data:** strictly **public**, safe-route only, **no PHI/PII ever**.
- **Stack:** SQLite source of truth → a static HTML page (`frontend/index.html`)
  that reads a generated `frontend/data.js`. No server, no internet to use it —
  double-click `index.html`.

**Current state:** 11 buckets, ~469 provider orgs, **1,751 searchable ZIPs**
(every KS+MO ZIP), ~98% direct phones (211 fallback otherwise), distance-sorted,
per-provider-accurate service areas. All committed, FK clean.

---

## 2. Quick start

```bash
cd ~/kansas-missouri-ssbci-resources

./build_real.sh          # rebuild KS+MO (default)
STATES=TX ./build_real.sh  # build a single other state
STATES=TX,OK,AR ./build_real.sh  # multi-state build

open frontend/index.html # use it: type a ZIP, see resources, print

./build.sh               # alt: the old [SAMPLE] demo (fake data, banner)
```

**GitHub remote:** `https://github.com/jessicabutterhorn-dev/Resources-By-Zipcode.git`

`build_real.sh` runs, in order:
`schema → load_geography → load_zip_county → [connectors] → fill_phones →
needs_phone_report → load_zip_centroids → build_frontend → gen_credits`.

Requires `python3` + `sqlite3` (both standard on macOS). No pip installs.

---

## 3. How a search works (front-end behavior)

Type a ZIP → it resolves to its county(ies) → shows three tiers:

1. **Local listings** — grouped by category section (Food, Hygiene, Dental,
   Vision, Utility, Rent, Housing, Prescription, Pet Food, Transportation,
   Navigation), **nearest-first**.
   - **Walk-ins** (office in your county): show **"📍 X mi away"** (green ≤4 mi).
   - **Regional/area-wide** (serve your county from elsewhere): show **"Serves
     your county — call for services near you"**, no misleading far address.
   - Every card shows a **phone** (direct, or "Dial 211" fallback), website,
     hours, eligibility, and a source/confidence/date footer.
2. **Regional Resources** — area directories for your zone (Start Here STL, the
   regional United Way 211, etc.).
3. **Statewide help** — national/state referral tools (211, findhelp,
   BenefitsCheckUp, state SNAP/LIEAP apply lines).

---

## 4. The buckets + where each comes from

| Bucket | Source(s) |
|---|---|
| food | Operation Food Search (St. Louis), CAAGKC pantries (KC), MO Community Action Agencies, AAA senior meals |
| hygiene | curated St. Louis providers (unverified-flagged) |
| dental | free-dental workflow (free + non-profit only) |
| vision | free-vision workflow (Lions, free clinics, New Eyes, EyeCare America) |
| prescription | free/charitable workflow (Extra Help/LIS, SHICK, MO SHIP, MORx, charitable pharmacies, NeedyMeds) |
| rent | nonprofit/govt workflow (Salvation Army, Catholic Charities, CAAs, MHDC/KHRC) |
| pet_food | free pet-food workflow (PRCKC, humane societies, Bi-State Pet Food Pantry) |
| utility | MO Community Action Agencies (LIHEAP delivery) |
| housing | HUD Housing Counseling Agencies (**national** — all 50 states) |
| gas_transport | Area Agencies on Aging (senior transport) |
| navigation | MO Job Centers, AAA info & referral |

Connectors live in `pipeline/connectors/`. Source register: `pipeline/config/sources.yaml`.

---

## 5. HARD RULES (do not break — these keep it trustworthy)

1. **Safe-route sourcing only.** Official/open/licensed datasets + .gov +
   robots-permitted org pages. No gray-area bulk scraping. Check robots.txt
   before any automated fetch.
2. **Zero PHI/PII.** Only public org info. The schema has no field able to hold
   member data → HIPAA out of scope by construction.
3. **Verify everything.** Every record carries `source_url + date_checked +
   confidence`. Records that can't be verified are flagged `unverified` (amber
   badge), never presented as fact.
4. **Free + non-profit only** for dental/vision/pet-food (her rule) — NOT
   sliding-scale, NOT for-profit, NOT dental/optometry schools.
5. **Accurate service areas — NEVER zone-expand.** A provider shows ONLY for the
   counties it actually serves: a walk-in `site` = its office county; a `program`
   = its resolved scope (`national` / `statewide_MO` / `statewide_KS` /
   `statewide_both` / specific `counties`). Unscoped records are **skipped**, not
   over-claimed. (Sending someone to a provider that doesn't serve them is the
   cardinal sin.)
6. **Phone on every card.** Real number where found + two-source-verified;
   otherwise the free **211** line. Gaps tracked in `docs/NEEDS_PHONE.md`.
7. **Connectors MUST NOT write `zip_county`.** The Census ZCTA→county crosswalk
   (`load_zip_county.py`) is the sole authority. (Connectors trusting record ZIP
   fields caused a mistyped ZIP to phantom-link a rural town to a far metro.)
8. **No "what you're losing" framing.** Show available resources only.

---

## 6. How to ADD A NEW free/charitable bucket (the recipe)

This is the proven pattern (used for dental, vision, prescription, rent, pet_food):

1. **Add the bucket** to the `resource_bucket` CHECK in `db/schema.sql`, a label
   in `pipeline/build_frontend.py` (`BUCKET_LABELS`), and a section in
   `frontend/index.html` (`SECTIONS`).
2. **Run a find+verify workflow** (multi-agent): per-zone search → adversarial
   verify (reject anything off-criteria; honest empty zones OK). Save results to
   `data/<bucket>_records.json`. (See the workflow scripts under
   `.../workflows/scripts/` — e.g. `free-dental`, `free-vision`.)
3. **Resolve service areas** for `program` + address-less records (the
   `fix-service-areas` workflow → sets `service_scope` + `served_counties`).
4. **Load** with the generic connector:
   ```bash
   python3 pipeline/connectors/free_resource.py \
     --bucket <bucket> --records data/<bucket>_records.json \
     --source-id <id> --source-name "<name>" \
     --service-name "<service label>" --dir-url <fallback url>
   ```
   Add that line to `build_real.sh`.
5. **Rebuild** (`./build_real.sh`), then run the QA checks (§8).

Record shape (per item): `{name, kind:"site"|"program", address, city, state,
zip, phone, website, what, source_url, confidence}`. Sites with a street address
geocode to their office county; programs use `service_scope`.

---

## 7. File map

```
build_real.sh              one-command full rebuild (real data)
build.sh                   sample-data demo build
db/
  schema.sql               SQLite schema (HSDS-aligned + geo spine + provenance)
  seed.sql                 fictional [SAMPLE] rows (demo only)
  resources.db             built DB (gitignored)
pipeline/
  load_geography.py        counties + county_zone (Census); accepts --states XX,YY (default KS,MO)
  load_zip_county.py       AUTHORITATIVE ZIP->county crosswalk (Census ZCTA); national by design
  load_zip_centroids.py    ZIP lat/lon (Census gazetteer) for distance; national by design
  connectors/              one file per data source (+ generic free_resource.py)
  fill_phones.py           backfills phones from data/phone_overrides.json
  needs_phone_report.py    -> docs/NEEDS_PHONE.md worklist
  build_frontend.py        DB -> frontend/data.js (distance, dedup, serves-area)
  gen_credits.py           -> frontend/credits.html (attribution + privacy)
  config/sources.yaml      source register (license, access lane, enabled)
frontend/
  index.html               the searchable, printable page
  data.js                  generated data (do not hand-edit)
  credits.html             generated
data/
  zones.json               6-zone -> county map
  zip_centroids.json       generated
  *_records.json           workflow outputs per bucket (rent/rx/dental/...)
  phone_overrides.json     org_id -> phone (survives rebuilds)
  referrals.json           statewide + regional link-outs
docs/
  00..05-*.md              original research briefs
  GOVERNANCE_ACTIONS.md    plan to unlock gated bulk sources
  NEEDS_PHONE.md           orgs still needing a phone (auto-regenerated)
  FRONTEND_PLAN.md, PIPELINE_PLAN.md
PROJECT_HANDOFF.md         <- this file
```

---

## 8. QA checks to re-run after changes

After any rebuild, sanity-check:

- `sqlite3 db/resources.db "PRAGMA foreign_key_check;"` → must be empty.
- No walk-in distance should exceed ~30 mi cross-county (same-county metro spread
  up to ~30 mi is fine).
- No in-ZIP duplicate (same org + bucket twice).
- Spot-check a rural ZIP (e.g. 66801 Emporia, 63701 Cape Girardeau), a metro
  (64111 KC), and a bi-state ZIP (66101 KCK) — each should return sensible,
  near-first, deduped results with phones.
- Every active service must be reachable by at least one county (no invisibles).

(The session's full QA script lives in the git history of this commit message:
"fix(QA): authoritative ZIP->county + cross-ZIP dedup".)

---

## 9. What's left / next steps (ranked)

1. **Governance (biggest unlock, non-code).** See `docs/GOVERNANCE_ACTIONS.md`:
   - IP/ownership sign-off (gates public release; enterprise vs personal repo).
   - 211 NDP feed keys via the 4 local United Ways → statewide directory depth.
   - Feeding America HSDS feed → all food banks/pantries.
   Connectors for these are stubbed in `sources.yaml` (enabled=false until keys).
2. **The last ~6 phones** — team worklist in `docs/NEEDS_PHONE.md` (verify on a
   second source before adding to `phone_overrides.json`).
3. **Stakeholder polish** — a short "About / How to use" intro on the page; this
   is what you take into the room for the governance sign-off.
4. **More food density** — once Feeding America HSDS lands (per-food-bank
   scraping was a dead end; Harvesters/KFB are JS widgets).

---

## 10. Multi-agent workflow patterns used (for reference)

The heavy data work used multi-agent workflows (each: fan out per zone/item →
adversarially verify → return structured records). Reusable shapes:
- **find + verify** (dental/vision/rx/rent/petfood): per-zone search, then a
  skeptic agent rejects anything off-criteria.
- **resolve service areas** (`fix-service-areas`): per record, classify
  national/statewide/county-list from its stated coverage.
- **authoritative map** (`aaa-county-map`): assign every county to exactly one
  agency from an official source.
- **two-source phone verify** (`verify-phones`): confirm a number on two
  independent sources before accepting.

Scripts persist under the session's `workflows/scripts/` dir; re-invoke with
`{scriptPath, resumeFromRunId}` to reuse cached agent results.

---

_Built on open data, safe-route only, no member data. Honest by design: it shows
what it can verify, flags what it can't, and never sends someone where they
aren't served._

---

## 11. Direction update (2026-06-26): Enterprise Snowflake pivot

Decisions from a planning session. These **supersede** the "public hosted
launch" assumption in §9 for the primary use case.

### 11.1 Why the pivot

The subject matter (SSBCI Medicare benefit loss, CMS-4208-F eff. 1/1/2027, ~75%+
lose the flex card for food/utility/rent/transport/gas) is squarely the
employer's business. A personal public launch raises an **IP/ownership question**
(own-time/own-computer helps, and KS K.S.A. 44-130 + MO law limit employer claims
on personal inventions, but the "relates to employer business" exception is the
gray part). **Building it inside Aetna dissolves that question** — it becomes a
sanctioned work product — and lets Aetna legal sign the gated-feed agreements
(§9.1–9.2) that an individual can't.

> Nothing is triggered while the repo stays **private and offline** (`file://`
> demo). The only deliberate step is *public hosting* — which the pivot removes
> from the critical path. Until any ruling: keep repo private; never push to a
> personal GitHub with enterprise credentials.

### 11.2 Who uses it + how (this reframes the product)

Users = **internal Aetna staff**: Account Managers, Broker Managers, Field Sales
Reps, internal staff. They **print** sheets and hand them to agents visiting
clients / low-income housing. The **end consumer is offline, holding paper.**

→ The app is a **single-ZIP print generator**, not a member-facing website:

```
staff types 1 ZIP → one clean printable page → File > Print, N copies → done
```

- **No** batch/territory packets, **no** member logins, **no** copy-count logic
  (the printer handles copies), **no** public site, **no** sharding/CDN/46MB
  problem — all moot for the internal print use.
- **DO** nail: one ZIP → one page; phone-first; big text (older/low-vision);
  print-clean CSS (no nav/buttons on paper); nearest-first, deduped, phone on
  every card (already built); footer **"Verified [Month YYYY] — call 211 if a
  number changed"** so frozen paper self-discloses staleness (uses `date_checked`).
- **PHI rule survives the paper hop:** the sheet is keyed only to a ZIP, carries
  zero member data — nothing personal leaves the building even when left at an
  apartment. Keep it that way in Snowflake: never join to member/claims tables.

### 11.3 Architecture mapping (personal → enterprise)

| Now (personal) | Enterprise (Snowflake/intranet) |
|---|---|
| SQLite source of truth | Snowflake tables |
| Static `index.html` + `data.js` | **Streamlit-in-Snowflake** app (built-in UI) |
| Double-click a file | Brokers hit an internal URL |
| Hand-find data via Claude Code | Sanctioned feeds (Half 1) + vetted-JSON load (Half 2) |

**Getting internet data IN — split in two:**
- **Half 1 — structured feeds → pull into Snowflake** via **External Access
  Integration** (+ network rule whitelisting endpoints + secret for the key).
  Fits Census (static files → stage), 211 NDP HSDS, Feeding America HSDS. Aetna
  legal can sign the §9 agreements.
- **Half 2 — org discovery (the Claude-Code find+verify work)** stays a research
  step producing **reviewed JSON**, then loaded to Snowflake (same
  `*_records.json` → table pattern). Don't scrape from inside the warehouse.

**Tradeoffs accepted:** internal-only (members don't access directly — paper is
the distribution layer; a public member version is a separate later decision);
work moves onto Aetna governance/timeline; PHI design stays sacred.

### 11.4 Border-ZIP (KC metro) — already solved, don't break it

`build_frontend.py:64-87` already collects **every county FIPS a ZIP touches**
and returns services covering any of them — FIPS is state-agnostic, so bi-state
ZIPs (66101 KCK, 64111 KC-MO, 64501 St. Joseph) already pull both states' orgs.
**Rule when partitioning data: key on ZIP→all-FIPS, never `WHERE state=`.** Any
state label (e.g. a `/kansas` view) is cosmetic framing only, never a results
filter. Add a QA assertion that bi-state ZIPs return both states.

### 11.5 How to transfer to Snowflake (migration recipe)

Data is tiny (~2.6MB) → the move is minutes once access exists.

- **Step 0 — access (from platform team):** a database+schema to own, a warehouse
  (XS fine), a role that can `CREATE TABLE` + `CREATE STREAMLIT`. **Confirm
  whether External Access Integrations are enabled** or all outbound is blocked —
  that decides auto-pull feeds vs. manual file loads.
- **Step 1 — schema:** translate `db/schema.sql` (SQLite) → Snowflake DDL
  (`INTEGER`→`NUMBER`, drop `PRAGMA`, etc.), run once.
- **Step 2 — data:** export tables → CSV, drag into **Snowsight** Load UI; **or**
  load existing `*_records.json` directly via `COPY INTO` + `PARSE_JSON`; **or**
  scripted `snowsql PUT` + `COPY INTO` once automating monthly.
- **Step 3 — app:** rewrite `index.html`/`data.js` logic as a **Streamlit-in-
  Snowflake** Python file (`st.text_input` ZIP → SQL multi-FIPS lookup → render
  cards → print CSS).
- **Step 4 — feeds (later):** External Access Integration for 211 / Feeding
  America after data loads and agreements sign.

### 11.6 Next actions (ranked)

1. **Get Snowflake access** (Step 0) — gates everything; ask the platform team,
   including the External-Access-enabled question.
2. **Build the three migration artifacts** (offered, not yet built):
   `schema.sql`→Snowflake DDL; a SQLite→CSV/JSON export script; a
   Streamlit-in-Snowflake skeleton (ZIP search + print page).
3. **(Optional, parallel) read your own employment IP clause** so the
   personal-vs-work-product question is settled with facts, not worry.
4. Then: load data → stand up the Streamlit print page → add feeds via legal.

---

## 12. National expansion — status as of 2026-06-26

### 12.1 What's done

**Step 1 — Pipeline parameterized (committed, on GitHub main):**

The pipeline now accepts a `STATES` env var so any state combination builds cleanly:

```bash
STATES=TX ./build_real.sh         # Texas only
STATES=TX,OK,AR ./build_real.sh   # multi-state
./build_real.sh                   # KS+MO (default unchanged)
```

Files changed:
- `pipeline/load_geography.py` — `--states XX,YY` arg; removes KS/MO hardcode
- `pipeline/connectors/hud_housing_counseling.py` — full 50-state FIPS map; dynamic ArcGIS WHERE clause; now truly national
- `pipeline/build_frontend.py` — `--states` arg filters output ZIPs to target states
- `build_real.sh` — threads `STATES` through all three above

`load_zip_county.py` and `load_zip_centroids.py` were already national — no change needed.

**HUD housing counseling is now fully national.** Run `STATES=TX ./build_real.sh` and Texas gets real HUD agency data immediately.

### 12.2 National source found for AAA (Step 2 — pending decision)

The Eldercare Locator search backend is an **ElasticSearch service at `esrv.acl.gov`** with read-only credentials embedded in the public JS bundle (intentional — all browser users receive them). This could replace the KS/MO-specific `aaa_seniors.py` with a single national connector covering all ~600 Area Agencies on Aging across all 50 states.

**Decision needed before building:** Use the public-in-JS credentials directly, or request official API access from ACL? Either way, the connector shape is known — same HSDS load pattern as the existing AAA connector.

### 12.3 What still needs work per new state

When you run `STATES=TX ./build_real.sh`, you get:
- ✅ All TX counties + ZIPs loaded
- ✅ TX HUD housing counseling agencies
- ⬜ AAA (meals/transport/navigation) — needs Step 2 decision above
- ⬜ LIHEAP/utility — `liheap_mo_caa.py` is MO-specific; needs a national CAA source (NASCSP publishes a national directory)
- ⬜ Food — no TX food pantry connector yet; national solution gated on Feeding America HSDS key
- ⬜ Dental/vision/rx/rent/pet_food — `data/*_records.json` files are KS/MO records only; need to run the find+verify workflow per new state before those buckets populate
- ⬜ `referrals.json` — still KS/MO 211 links; needs per-state entries
- ⬜ `zones.json` — KS/MO only; new states show `zone_id=null`, regional referrals won't display (resource lookup still works fine)

### 12.4 Recommended one-state pilot order

1. Pick a state with strong 211 coverage (e.g. TX or IL)
2. Decide the esrv.acl.gov/AAA question (§12.2)
3. Build AAA national connector → run `STATES=TX ./build_real.sh` → TX gets housing + AAA immediately
4. Run dental/vision/rx/rent/petfood find+verify workflow for TX (same workflow shapes as KS/MO, just different geography)
5. Add TX referrals entries to `referrals.json`
6. QA: same checks as §8 but with TX ZIPs
