## Reproducible Quarterly Refresh Pipeline

**Principle:** Ingest official/open sources -> normalize to HSDS -> geocode -> dedup -> verify (incl. PII tripwire) -> load SQLite -> rebuild static front-end. Fully scripted, idempotent, and logged in `refresh_log` so any quarter is reproducible from source + git commit.

### Cadence
- **Quarterly full refresh** (aligns with HUD ZIP crosswalk quarterly files and most agency snapshot cadences). Tag each run with a `refresh_quarter` (e.g. `2026Q3`).
- **Carrier benefits** refresh **annually at AEP** (plan-year flip) plus an out-of-cycle pull when CMS posts new Landscape/enrollment files — the 2027 loss event is the load-bearing trigger.

### Live vs snapshot per source (from DATA SOURCES brief)
- **Live API pull** (re-fetched each run): 211 National Data Platform (keyed, agreement-gated), data.mo.gov SODA, MSDIS/HUD Esri services, Feeding America HSDS feed, data.gov, Census Geocoder, HUD-USPS ZIP crosswalk API.
- **Quarterly snapshot** (versioned file checked into `data/snapshots/<quarter>/`): USDA ERS atlases, LIHEAP Clearinghouse + ACF contact listings, Eldercare Locator/ACL pages, KS DCF / MO DSS .gov pages, CMS MA Landscape/enrollment files.
- **Licensed-route, never scraped:** findhelp/Aunt Bertha, 211 NDP/local web directories — ingest only under executed agreement; otherwise single-fact manual corroboration only.

### Stages (each writes a `refresh_log` row)
1. **ingest** — Pull each source via its connector. Connector first asserts `source.robots_checked = 1` and `source.access_route` is permitted (open, or licensed-with-agreement). Open sources pull freely; licensed sources require an agreement flag in config or they are skipped (logged `status='skipped'`). Raw payloads land in `data/raw/<quarter>/<source>/`.
2. **normalize** — Map each source's records into HSDS objects (organization/service/location/service_at_location/phone/schedule/eligibility/service_area). Validate against the published HSDS JSON Schema. Strip any AIRS/211-LA taxonomy codes (replace with internal-open labels) unless a license is held. Re-key prose into fact fields; never copy descriptive text wholesale.
3. **geocode** — Census Geocoder: address -> lat/long + county FIPS. HUD-USPS crosswalk: ZIP -> county(ies) with allocation ratios (multi-county for Kansas City). Stamp `address.fips` and denormalize `address.zone_id` from `county_zone`.
4. **dedup** — Splink (DuckDB-backed) across feeds to cluster the same org/location appearing in multiple sources; write `organization.dedup_cluster`. Merge corroborating sources into `record_provenance` so a record covered by 2+ sources (incl. one .gov/official feed) can earn `confidence='high'`.
5. **verify** — Apply the confidence ladder and the **PII tripwire** (CI guard): reject any record bearing member-shaped fields (member ID, DOB, SSN, plan ID, claim, diagnosis); count rejects into `refresh_log.records_rejected`. Assert every fact-bearing row has `source_url + date_checked + confidence` and at least one `record_provenance` row. Fail the run if any record lacks provenance.
6. **load** — Build `directory.sqlite` from validated records (transactional; `PRAGMA foreign_keys=ON`). Load geography reference tables (county, zone, county_zone, zip_county, city_county) from the canonical zone JSON + HUD/Census files. Run the zone validator (105 KS + 115 MO entries, all unique) before load proceeds.
7. **build_frontend** — Copy the freshly built `directory.sqlite` into `frontend/`, regenerate `credits.html` from the `source` table, and emit a build manifest (git commit + quarter + per-source `date_checked`).

### Verification / confidence ladder (enforced in `verify`)
- `high` = corroborated by 2+ sources including one .gov/official feed (multiple `record_provenance` rows).
- `medium` = single official/open feed.
- `low` = single aggregator/secondary listing pending re-verify.
- `unverified` = hypothesis (e.g., carrier benefit names pre-SB-confirmation) — never shown without a visible flag.

### Reproducibility guarantees
- Snapshots are content-addressed/versioned in `data/snapshots/<quarter>/`; raw pulls archived in `data/raw/<quarter>/`. Re-running a quarter from its snapshots + the tagged git commit reproduces the same `directory.sqlite`.
- `refresh_log.git_commit` ties each output to code state. Source license/attribution travels with every record via `source`.

### Folder layout (`pipeline/` + siblings)
```
db/
  schema.sql                 # the SQLite schema (this deliverable)
  migrations/                # versioned schema changes
pipeline/
  config/
    sources.yaml             # per-source: url, license, access_route, refresh_mode, agreement_flag
    zones.json               # canonical zone->county mapping (from ZONE SPLIT brief)
  connectors/                # one module per source (211_ndp, usda_ers, liheap, hud_zip, census_geo, data_mo, ...)
  ingest.py
  normalize_hsds.py          # map->HSDS + JSON-Schema validate + strip AIRS codes
  geocode.py                 # Census geocoder + HUD crosswalk -> fips/zone
  dedup.py                   # Splink clustering
  verify.py                  # confidence ladder + PII tripwire (CI-runnable standalone)
  load_sqlite.py             # build directory.sqlite (runs zone validator first)
  build_frontend.py          # copy db + regen credits.html
  run_refresh.py             # orchestrates stages, writes refresh_log
data/
  raw/<quarter>/<source>/    # archived raw pulls
  snapshots/<quarter>/       # versioned official snapshots
docs/
  license_register.md        # per-source license table (compliance §3)
  attribution_credits.md     # source -> credit strings
  hipaa_not_applicable.md    # structural rationale
agents/
  collector_prompt_pack.md   # the 6-zone collector prompt (parameterized)
frontend/                    # static site (see frontend_plan)
```

### CI checks (block merge / block load)
- HSDS JSON-Schema validation on all normalized records.
- **PII tripwire**: schema introspection + per-record scan rejects any member-shaped field; build fails on any hit.
- Provenance assertion: no fact-bearing row without `source_url + date_checked + confidence` and a `record_provenance` row.
- Zone validator: exactly 105 KS + 115 MO (incl. St. Louis City) jurisdictions, each in one zone.
- Robots/ToS gate: no connector runs against a source whose `robots_checked != 1` or whose `access_route` isn't permitted.
