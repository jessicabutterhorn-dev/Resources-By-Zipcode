-- =============================================================================
-- KS + MO SSBCI Social-Service Provider Directory — SQLite Schema
-- Source of truth for: static HTML/sql.js front-end + quarterly refresh pipeline.
-- Aligned to OpenReferral HSDS 3.x (organization/service/location/service_at_location)
-- with added provenance/verification on every record, ZIP->county->zone mapping,
-- and a carrier_benefits layer for "you are losing X -> here are local replacements".
--
-- HARD CONSTRAINTS ENFORCED STRUCTURALLY:
--   * ZERO PHI / PII: no table has a column capable of holding member identity,
--     DOB, SSN, plan/member ID, claim, or diagnosis. (PII tripwire = CI test,
--     see pipeline_plan; the schema itself simply offers no such column.)
--   * Every fact-bearing record carries source_url + date_checked + confidence
--     via a mandatory row in the `source` table referenced by source_id.
--   * Per-source license/attribution tracked in `source`.
--
-- Conventions: TEXT ids (UUID/slug). Dates ISO-8601 'YYYY-MM-DD'. Booleans 0/1.
-- PRAGMA foreign_keys = ON; must be set by the loader each connection.
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- PROVENANCE / VERIFICATION (referenced by virtually every fact-bearing table)
-- -----------------------------------------------------------------------------

-- A source = one ingest event/feed/page that a fact was extracted from.
-- Carries license + attribution per the compliance brief §3 register.
CREATE TABLE source (
    id                 TEXT PRIMARY KEY,                 -- uuid
    source_name        TEXT NOT NULL,                    -- e.g. "211 NDP - UW Greater KC", "USDA SNAP Retailer Locator"
    source_type        TEXT NOT NULL                     -- ingest lane
        CHECK (source_type IN (
            'gov_open_data','hsds_211_feed','feeding_america_hsds','findhelp_licensed',
            'gov_web_page','cms_landscape','cms_plan_finder','carrier_sb_eoc',
            'carrier_marketing_page','manual_verify','other')),
    publisher          TEXT,                             -- org that publishes the source
    source_url         TEXT NOT NULL,                    -- canonical URL of the source
    tos_url            TEXT,                             -- terms-of-service URL if any
    robots_checked     INTEGER NOT NULL DEFAULT 0        -- 1 = robots.txt + ToS confirmed permissive
        CHECK (robots_checked IN (0,1)),
    license            TEXT NOT NULL,                    -- e.g. 'CC BY 4.0','CC0','US-Gov-PublicDomain','HSDS-CC-BY-SA-4.0','proprietary-licensed','agency-open'
    attribution_text   TEXT,                             -- exact credit string to render on credits page
    attribution_required INTEGER NOT NULL DEFAULT 0
        CHECK (attribution_required IN (0,1)),
    redistribution_ok  INTEGER                           -- 1 yes / 0 no / NULL unknown-needs-confirm
        CHECK (redistribution_ok IN (0,1)),
    access_route       TEXT NOT NULL DEFAULT 'open'      -- safe-route lane gating
        CHECK (access_route IN ('open','licensed','agreement_required')),
    refresh_mode       TEXT NOT NULL DEFAULT 'snapshot'
        CHECK (refresh_mode IN ('live_api','snapshot')),
    date_checked       TEXT NOT NULL,                    -- ISO date this source was last verified
    confidence         TEXT NOT NULL                     -- per-source baseline confidence
        CHECK (confidence IN ('high','medium','low','unverified')),
    notes              TEXT
);
CREATE INDEX idx_source_type   ON source(source_type);
CREATE INDEX idx_source_route  ON source(access_route);
CREATE INDEX idx_source_checked ON source(date_checked);

-- Reusable verification stamp applied to any record. A record may be corroborated
-- by multiple sources (this is how 'high' confidence = 2+ sources incl. one .gov).
-- record_table/record_id is a soft polymorphic pointer (SQLite has no cross-table FK).
CREATE TABLE record_provenance (
    id            TEXT PRIMARY KEY,                       -- uuid
    record_table  TEXT NOT NULL,                          -- e.g. 'organization','service','location','carrier_benefit'
    record_id     TEXT NOT NULL,
    source_id     TEXT NOT NULL REFERENCES source(id) ON DELETE RESTRICT,
    source_url    TEXT NOT NULL,                          -- exact URL of the fact (may be deeper than source.source_url)
    date_checked  TEXT NOT NULL,                          -- ISO date
    confidence    TEXT NOT NULL
        CHECK (confidence IN ('high','medium','low','unverified')),
    extracted_by  TEXT NOT NULL DEFAULT 'human'
        CHECK (extracted_by IN ('human','automated')),
    method        TEXT,                                   -- 'api_pull','hsds_feed','manual_keying','corroboration'
    notes         TEXT,
    UNIQUE (record_table, record_id, source_id)
);
CREATE INDEX idx_prov_record ON record_provenance(record_table, record_id);
CREATE INDEX idx_prov_source ON record_provenance(source_id);

-- -----------------------------------------------------------------------------
-- GEOGRAPHY: ZIP -> county -> collection zone  (HUD crosswalk + Census FIPS)
-- Convention (per user memory): bare city names, MO/KS, one row per city-county
-- pair, Kansas City spans multiple counties.
-- -----------------------------------------------------------------------------

-- Canonical county list (Census ANSI/FIPS). 105 KS + 114 MO + St. Louis City(29510).
CREATE TABLE county (
    fips        TEXT PRIMARY KEY,                          -- 5-digit state+county FIPS
    county_name TEXT NOT NULL,                             -- bare name, no "County" suffix
    state       TEXT NOT NULL CHECK (state IN ('KS','MO')),
    is_independent_city INTEGER NOT NULL DEFAULT 0         -- St. Louis City = 1
        CHECK (is_independent_city IN (0,1)),
    population_2020 INTEGER,                               -- for workload balancing
    UNIQUE (county_name, state)
);
CREATE INDEX idx_county_state ON county(state);

-- The 6 collection zones (from ZONE SPLIT brief; JSON is canonical loader input).
CREATE TABLE zone (
    zone_id          INTEGER PRIMARY KEY,                  -- 1..6
    zone_name        TEXT NOT NULL,
    line_crossing    INTEGER NOT NULL DEFAULT 0 CHECK (line_crossing IN (0,1)),
    approx_population INTEGER,
    major_metros     TEXT                                  -- JSON array string
);

-- County -> zone assignment. Each county in exactly one zone (enforced by PK on fips).
CREATE TABLE county_zone (
    fips    TEXT PRIMARY KEY REFERENCES county(fips) ON DELETE CASCADE,
    zone_id INTEGER NOT NULL REFERENCES zone(zone_id) ON DELETE RESTRICT
);
CREATE INDEX idx_county_zone_zone ON county_zone(zone_id);

-- ZIP -> county crosswalk (HUD-USPS). A ZIP may span counties (Kansas City);
-- res_ratio is HUD's residential allocation ratio. PK is the (zip,county) pair.
CREATE TABLE zip_county (
    zip          TEXT NOT NULL,                            -- 5-digit ZIP
    fips         TEXT NOT NULL REFERENCES county(fips) ON DELETE CASCADE,
    res_ratio    REAL,                                     -- HUD residential allocation ratio
    bus_ratio    REAL,                                     -- business allocation ratio
    tot_ratio    REAL,                                     -- total allocation ratio
    is_primary   INTEGER NOT NULL DEFAULT 0                -- 1 = dominant county for the ZIP
        CHECK (is_primary IN (0,1)),
    crosswalk_vintage TEXT,                                -- e.g. '2026Q1' (HUD quarterly file)
    source_id    TEXT NOT NULL REFERENCES source(id) ON DELETE RESTRICT,
    PRIMARY KEY (zip, fips)
);
CREATE INDEX idx_zip_county_zip  ON zip_county(zip);
CREATE INDEX idx_zip_county_fips ON zip_county(fips);

-- City <-> county pairs (bare city names; KC appears once per county it spans).
CREATE TABLE city_county (
    id          TEXT PRIMARY KEY,
    city_name   TEXT NOT NULL,                             -- bare name
    state       TEXT NOT NULL CHECK (state IN ('KS','MO')),
    fips        TEXT NOT NULL REFERENCES county(fips) ON DELETE CASCADE,
    UNIQUE (city_name, state, fips)
);
CREATE INDEX idx_city_county_city ON city_county(city_name, state);

-- Resolved view: ZIP -> zone (for front-end "enter your ZIP" lookup).
CREATE VIEW v_zip_zone AS
SELECT zc.zip, zc.fips, c.county_name, c.state, zc.res_ratio, zc.is_primary,
       cz.zone_id, z.zone_name
FROM zip_county zc
JOIN county c       ON c.fips = zc.fips
JOIN county_zone cz ON cz.fips = zc.fips
JOIN zone z         ON z.zone_id = cz.zone_id;

-- -----------------------------------------------------------------------------
-- HSDS CORE: organization / service / location / service_at_location
-- (provider-side directory — populated only via SAFE ROUTE sources)
-- -----------------------------------------------------------------------------

CREATE TABLE organization (
    id            TEXT PRIMARY KEY,                        -- uuid (HSDS organization.id)
    name          TEXT NOT NULL,
    alternate_name TEXT,
    description   TEXT,                                    -- re-keyed facts, not copied prose
    email         TEXT,                                    -- PUBLIC org email only
    website       TEXT,
    tax_status    TEXT,                                    -- e.g. nonprofit/gov
    year_incorporated INTEGER,
    -- provenance (also corroborated via record_provenance for multi-source)
    source_id     TEXT NOT NULL REFERENCES source(id) ON DELETE RESTRICT,
    source_url    TEXT NOT NULL,
    date_checked  TEXT NOT NULL,
    confidence    TEXT NOT NULL CHECK (confidence IN ('high','medium','low','unverified')),
    hsds_org_id   TEXT,                                    -- upstream HSDS id if mapped from a feed
    dedup_cluster TEXT,                                    -- Splink/dedupe cluster id for cross-feed merge
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_org_name    ON organization(name);
CREATE INDEX idx_org_cluster ON organization(dedup_cluster);

CREATE TABLE location (
    id             TEXT PRIMARY KEY,                       -- uuid (HSDS location.id)
    organization_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    name           TEXT,
    location_type  TEXT,                                   -- 'physical','postal','virtual'
    latitude       REAL,                                   -- Census geocoder
    longitude      REAL,
    transportation TEXT,
    source_id      TEXT NOT NULL REFERENCES source(id) ON DELETE RESTRICT,
    source_url     TEXT NOT NULL,
    date_checked   TEXT NOT NULL,
    confidence     TEXT NOT NULL CHECK (confidence IN ('high','medium','low','unverified'))
);
CREATE INDEX idx_loc_org ON location(organization_id);

-- HSDS address (1+ per location). Holds the geocoded FIPS -> joins to zone.
CREATE TABLE address (
    id           TEXT PRIMARY KEY,
    location_id  TEXT NOT NULL REFERENCES location(id) ON DELETE CASCADE,
    address_type TEXT DEFAULT 'physical',                  -- 'physical'/'postal'
    address_1    TEXT,
    address_2    TEXT,
    city         TEXT,                                     -- bare city name
    state_province TEXT CHECK (state_province IN ('KS','MO',NULL)),
    postal_code  TEXT,                                     -- ZIP
    country      TEXT DEFAULT 'US',
    fips         TEXT REFERENCES county(fips),             -- geocoded county (Census)
    zone_id      INTEGER REFERENCES zone(zone_id)          -- denormalized for fast filter
);
CREATE INDEX idx_addr_location ON address(location_id);
CREATE INDEX idx_addr_zip      ON address(postal_code);
CREATE INDEX idx_addr_fips     ON address(fips);
CREATE INDEX idx_addr_zone     ON address(zone_id);

CREATE TABLE service (
    id              TEXT PRIMARY KEY,                      -- uuid (HSDS service.id)
    organization_id TEXT NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    alternate_name  TEXT,
    description     TEXT,                                  -- re-keyed facts only
    url             TEXT,
    email           TEXT,
    status          TEXT DEFAULT 'active'                  -- HSDS service.status
        CHECK (status IN ('active','inactive','defunct','temporarily closed')),
    -- our replacement-resource bucket (drives benefit->resource matching)
    resource_bucket TEXT NOT NULL
        CHECK (resource_bucket IN ('food','utility','rent','pet_food',
                                   'gas_transport','prescription','housing','navigation')),
    application_process TEXT,                              -- how to apply (facts)
    fees                TEXT,
    source_id     TEXT NOT NULL REFERENCES source(id) ON DELETE RESTRICT,
    source_url    TEXT NOT NULL,
    date_checked  TEXT NOT NULL,
    confidence    TEXT NOT NULL CHECK (confidence IN ('high','medium','low','unverified')),
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_service_org    ON service(organization_id);
CREATE INDEX idx_service_bucket ON service(resource_bucket);

-- HSDS service_at_location: which service is offered at which location.
CREATE TABLE service_at_location (
    id          TEXT PRIMARY KEY,
    service_id  TEXT NOT NULL REFERENCES service(id) ON DELETE CASCADE,
    location_id TEXT NOT NULL REFERENCES location(id) ON DELETE CASCADE,
    description TEXT,
    UNIQUE (service_id, location_id)
);
CREATE INDEX idx_sal_service  ON service_at_location(service_id);
CREATE INDEX idx_sal_location ON service_at_location(location_id);

-- HSDS phone (public org phones only).
CREATE TABLE phone (
    id          TEXT PRIMARY KEY,
    -- attach to org, service, or location (soft polymorphic; exactly one set)
    organization_id TEXT REFERENCES organization(id) ON DELETE CASCADE,
    service_id      TEXT REFERENCES service(id) ON DELETE CASCADE,
    location_id     TEXT REFERENCES location(id) ON DELETE CASCADE,
    number      TEXT NOT NULL,
    extension   TEXT,
    type        TEXT,                                      -- 'voice','tty','hotline'
    description TEXT
);
CREATE INDEX idx_phone_org ON phone(organization_id);
CREATE INDEX idx_phone_svc ON phone(service_id);
CREATE INDEX idx_phone_loc ON phone(location_id);

-- HSDS schedule (hours). Stored as facts; supports human-readable + structured.
CREATE TABLE schedule (
    id          TEXT PRIMARY KEY,
    service_id  TEXT REFERENCES service(id) ON DELETE CASCADE,
    location_id TEXT REFERENCES location(id) ON DELETE CASCADE,
    valid_from  TEXT,
    valid_to    TEXT,
    opens_at    TEXT,                                      -- 'HH:MM'
    closes_at   TEXT,
    byday       TEXT,                                      -- 'MO,TU,WE' iCal-style
    description TEXT,                                      -- human-readable hours
    freq        TEXT                                       -- 'WEEKLY' etc.
);
CREATE INDEX idx_sched_service  ON schedule(service_id);
CREATE INDEX idx_sched_location ON schedule(location_id);

-- HSDS eligibility (who qualifies — public program rules, NOT member data).
CREATE TABLE eligibility (
    id          TEXT PRIMARY KEY,
    service_id  TEXT NOT NULL REFERENCES service(id) ON DELETE CASCADE,
    description TEXT,                                      -- e.g. 'income <=150% FPL', 'seniors 60+'
    min_age     INTEGER,
    max_age     INTEGER
);
CREATE INDEX idx_elig_service ON eligibility(service_id);

-- HSDS service_area (geographic coverage of a service).
CREATE TABLE service_area (
    id          TEXT PRIMARY KEY,
    service_id  TEXT NOT NULL REFERENCES service(id) ON DELETE CASCADE,
    extent_type TEXT,                                      -- 'county','zip','state','radius'
    fips        TEXT REFERENCES county(fips),              -- when county-scoped
    zip         TEXT,                                      -- when zip-scoped
    description TEXT
);
CREATE INDEX idx_sa_service ON service_area(service_id);
CREATE INDEX idx_sa_fips    ON service_area(fips);

-- HSDS taxonomy_term — OPEN labels only. AIRS/211LA codes MUST NOT be stored here
-- unless a license is held; the loader strips AIRS codes (see compliance §1A).
CREATE TABLE taxonomy_term (
    id           TEXT PRIMARY KEY,
    term         TEXT NOT NULL,                            -- our open category label
    vocabulary   TEXT NOT NULL DEFAULT 'internal-open'     -- never 'AIRS' unless licensed
        CHECK (vocabulary IN ('internal-open','openeligibility','hsds-open')),
    parent_id    TEXT REFERENCES taxonomy_term(id),
    description  TEXT
);

CREATE TABLE service_taxonomy (
    service_id      TEXT NOT NULL REFERENCES service(id) ON DELETE CASCADE,
    taxonomy_term_id TEXT NOT NULL REFERENCES taxonomy_term(id) ON DELETE CASCADE,
    PRIMARY KEY (service_id, taxonomy_term_id)
);

-- -----------------------------------------------------------------------------
-- CARRIER BENEFITS LAYER ("you are losing X")
-- Grain = plan-year x PBP x benefit. Public CMS + carrier SB/EOC facts only.
-- -----------------------------------------------------------------------------

CREATE TABLE carrier_benefit (
    id                  TEXT PRIMARY KEY,                  -- uuid
    parent_company      TEXT NOT NULL,                     -- 'Centene'
    carrier_brand       TEXT NOT NULL,                     -- 'Wellcare'
    plan_name           TEXT,
    cms_contract_id     TEXT,                              -- H-contract e.g. 'H1234'
    cms_pbp_id          TEXT,                              -- plan benefit package #
    plan_type           TEXT CHECK (plan_type IN ('HMO','PPO','D-SNP','C-SNP','MMP','other',NULL)),
    plan_year           INTEGER NOT NULL,                  -- 2026 / 2027
    state               TEXT CHECK (state IN ('KS','MO','BOTH')),
    benefit_marketing_name TEXT,                           -- 'Healthy Options Allowance'
    benefit_card_vendor TEXT,                              -- 'NationsBenefits','Incomm','OTCHS'
    ssbci_flag          INTEGER NOT NULL DEFAULT 0         -- chronically-ill-only benefit
        CHECK (ssbci_flag IN (0,1)),
    eligibility_conditions TEXT,                           -- qualifying chronic conditions / dual status
    allowance_amount    REAL,                              -- $ per period
    allowance_period    TEXT CHECK (allowance_period IN ('monthly','quarterly','annual',NULL)),
    allowance_rollover  INTEGER CHECK (allowance_rollover IN (0,1,NULL)),
    redemption_channels TEXT,                              -- JSON array string
    ends_effective_date TEXT,                              -- target 2027-01-01
    loss_summary        TEXT,                              -- plain-language "what you're losing"
    -- provenance (mandatory)
    source_id           TEXT NOT NULL REFERENCES source(id) ON DELETE RESTRICT,
    source_url          TEXT NOT NULL,
    source_doc_type     TEXT NOT NULL
        CHECK (source_doc_type IN ('SB','EOC','plan-page','CMS-PlanFinder','landscape-file','secondary')),
    date_checked        TEXT NOT NULL,
    confidence          TEXT NOT NULL
        CHECK (confidence IN ('high','medium','low','unverified')),
    license_attribution TEXT,                              -- 'CMS public-domain' / carrier ToS note
    extracted_by        TEXT NOT NULL DEFAULT 'human'
        CHECK (extracted_by IN ('human','automated')),
    notes               TEXT,
    UNIQUE (cms_contract_id, cms_pbp_id, plan_year, benefit_marketing_name)
);
CREATE INDEX idx_cb_brand  ON carrier_benefit(carrier_brand);
CREATE INDEX idx_cb_year   ON carrier_benefit(plan_year);
CREATE INDEX idx_cb_state  ON carrier_benefit(state);
CREATE INDEX idx_cb_ssbci  ON carrier_benefit(ssbci_flag);

-- Counties a given plan/benefit covers (resolves BOTH-state + bistate Blue KC).
CREATE TABLE carrier_benefit_county (
    benefit_id TEXT NOT NULL REFERENCES carrier_benefit(id) ON DELETE CASCADE,
    fips       TEXT NOT NULL REFERENCES county(fips) ON DELETE CASCADE,
    PRIMARY KEY (benefit_id, fips)
);
CREATE INDEX idx_cbc_fips ON carrier_benefit_county(fips);

-- Which lost benefit category maps to which resource bucket (the bridge).
CREATE TABLE benefit_category (
    id          TEXT PRIMARY KEY,
    benefit_id  TEXT NOT NULL REFERENCES carrier_benefit(id) ON DELETE CASCADE,
    category    TEXT NOT NULL                              -- as named in the SB
        CHECK (category IN ('groceries','otc','utilities','rent','pet_food',
                            'transport_nonmedical','prescription','dental','vision','hearing','other')),
    resource_bucket TEXT NOT NULL                          -- where to send the member
        CHECK (resource_bucket IN ('food','utility','rent','pet_food',
                                   'gas_transport','prescription','housing','navigation')),
    ssbci_gated INTEGER NOT NULL DEFAULT 0 CHECK (ssbci_gated IN (0,1)),
    notes       TEXT
);
CREATE INDEX idx_bencat_benefit ON benefit_category(benefit_id);
CREATE INDEX idx_bencat_bucket  ON benefit_category(resource_bucket);

-- -----------------------------------------------------------------------------
-- REFRESH PIPELINE BOOKKEEPING
-- -----------------------------------------------------------------------------

CREATE TABLE refresh_log (
    id            TEXT PRIMARY KEY,
    run_started   TEXT NOT NULL,                           -- ISO timestamp
    run_finished  TEXT,
    refresh_quarter TEXT,                                  -- '2026Q3'
    source_id     TEXT REFERENCES source(id) ON DELETE SET NULL,
    stage         TEXT NOT NULL                            -- pipeline stage
        CHECK (stage IN ('ingest','normalize','geocode','dedup','verify','load','build_frontend')),
    status        TEXT NOT NULL CHECK (status IN ('success','partial','failed','skipped')),
    records_in    INTEGER,
    records_out   INTEGER,
    records_rejected INTEGER,                              -- e.g. PII-tripwire rejects
    git_commit    TEXT,                                    -- reproducibility pointer
    message       TEXT
);
CREATE INDEX idx_refresh_quarter ON refresh_log(refresh_quarter);
CREATE INDEX idx_refresh_source  ON refresh_log(source_id);

-- -----------------------------------------------------------------------------
-- FRONT-END HELPER VIEW: ZIP -> lost benefits (by plan) -> local replacements
-- Front-end joins on the member's ZIP -> zone/county, then carrier_benefit_county
-- + benefit_category.resource_bucket -> service.resource_bucket in that zone.
-- -----------------------------------------------------------------------------
CREATE VIEW v_resource_by_zip AS
SELECT zz.zip, zz.zone_id, zz.fips, zz.county_name, zz.state,
       s.id AS service_id, s.name AS service_name, s.resource_bucket,
       o.id AS org_id, o.name AS org_name, o.website,
       a.address_1, a.city, a.postal_code,
       s.confidence, s.source_url, s.date_checked
FROM v_zip_zone zz
JOIN address a            ON a.zone_id = zz.zone_id AND a.fips = zz.fips
JOIN location l           ON l.id = a.location_id
JOIN service_at_location sal ON sal.location_id = l.id
JOIN service s            ON s.id = sal.service_id AND s.status = 'active'
JOIN organization o       ON o.id = s.organization_id;

CREATE VIEW v_losses_by_zip AS
SELECT zz.zip, zz.fips, zz.zone_id,
       cb.id AS benefit_id, cb.carrier_brand, cb.plan_name, cb.plan_year,
       cb.benefit_marketing_name, cb.ssbci_flag, cb.loss_summary,
       bc.category, bc.resource_bucket
FROM v_zip_zone zz
JOIN carrier_benefit_county cbc ON cbc.fips = zz.fips
JOIN carrier_benefit cb         ON cb.id = cbc.benefit_id
JOIN benefit_category bc        ON bc.benefit_id = cb.id;
