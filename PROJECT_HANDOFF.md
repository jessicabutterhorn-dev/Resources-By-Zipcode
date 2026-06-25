# KS + MO Community Resource Finder — Project Handoff

A pick-up-and-continue guide to the whole project: what it is, how to run it,
how it's built, the rules that keep it trustworthy, and what's left.

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

./build_real.sh          # rebuild everything from real open data (~5 min; geocodes)
open frontend/index.html # use it: type a ZIP, see resources, print

./build.sh               # alt: the old [SAMPLE] demo (fake data, banner)
```

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
| housing | HUD Housing Counseling Agencies (KS+MO) |
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
  load_geography.py        220 KS+MO counties + zones + county_zone (Census)
  load_zip_county.py       AUTHORITATIVE ZIP->county crosswalk (Census ZCTA)
  load_zip_centroids.py    ZIP lat/lon (Census gazetteer) for distance
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
