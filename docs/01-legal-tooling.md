I have everything needed. Here is the compliance and tooling brief.

---

# Compliance & Tooling Brief — KS/MO Public Social-Service Provider Directory

**Scope:** Plan + scaffold only. Public directory of food/utility/rent/pet-food/gas/prescription/housing-assistance providers for Medicare members in KS+MO losing SSBCI/flex/grocery-card benefits effective 1/1/2027. **Zero PHI/PII. Safe-route sourcing only.**

---

## 1. Compliance checklist

### A. Data licensing & ToS (the load-bearing risks)
- [ ] **Maintain a per-source license register** (see §3). Before ingesting any feed, record: source name, license, attribution requirement, redistribution permission, ToS URL, date checked, confidence flag. No record enters the DB without `source_url + date_checked + confidence`.
- [ ] **Prefer open/government feeds over aggregators.** Rank in this order: (1) `.gov` open data / agency APIs (Census, USDA, HUD, state agencies), (2) OpenReferral HSDS feeds published by 211s/United Ways, (3) findhelp/211 public listings — fact-extraction only, never bulk export.
- [ ] **Respect ToS as a contract, not a suggestion.** findhelp's ToS states the database is **proprietary "Findhelp Content"** and aggregated data IP is retained by findhelp ([findhelp ToS](https://www.auntbertha.com/legal/terms), [customer terms](https://company.findhelp.com/customerterms/)). Do **not** bulk-scrape or re-host findhelp/Aunt Bertha listings. Permitted: manually verifying a single org's public phone/address against findhelp as one of several corroborating sources, then storing the *fact* (not the page).
- [ ] **Do NOT embed the AIRS/211 LA Taxonomy.** It is copyrighted and **license-restricted to paid subscribers**, redistribution prohibited ([AIRS](https://www.airs.org/i4a/pages/index.cfm?pageid=3386), [211 LA terms](https://211la.wordpress.com/commonly-asked-questions/)). Use HSDS's open **taxonomy_term** structure with your own/openly-licensed category labels instead. If a 211 HSDS feed carries AIRS codes, store the org facts but strip/replace the taxonomy codes unless you hold a license.
- [ ] **Check robots.txt + ToS before any automated fetch.** No automated collection from any site that forbids it. This is a hard constraint.
- [ ] **Extract facts, not documents.** Facts (name, public phone, address, hours, eligibility) are generally not copyrightable; the *compilation/expression* on a source page can be. Re-key facts; never copy/paste descriptive prose wholesale.

### B. Attribution
- [ ] Build an **attribution/credits page** and per-record `source` field. CC BY sources (USDA SNAP locator, HSDS spec, most data.gov) **require visible attribution**; CC BY-SA (HSDS spec text) additionally requires share-alike on derivatives *of the spec*, not of your data records.
- [ ] If you reuse the HSDS **schema** as published, attribute Open Referral (CC BY-SA 4.0). Your *data* populated into HSDS is your own and not encumbered by SA.

### C. HIPAA — why it does not apply (document this rationale in-repo)
- This directory contains **only public organizational information** (org name, public phone, public address/email, public contact name, services, eligibility, hours). It contains **no individually identifiable health information of any member**.
- HIPAA's Privacy Rule attaches to **Protected Health Information (PHI)** created/received by covered entities/business associates *about individuals*. A public listing of food pantries is not PHI; it is comparable to a phone book. With **zero member data ingested or stored**, the database is **out of scope for HIPAA** by design.
- The protection is structural: enforce a schema that has **no fields capable of holding member/PII data**. Add a CI check that rejects any record containing member-shaped fields (member ID, DOB, SSN, plan ID, claim, diagnosis). Compliance-by-construction beats compliance-by-policy.

### D. Employer/Aetna governance — personal vs enterprise GitHub
- [ ] **Confirm IP ownership before committing.** If this work touches Aetna/CVS business (Medicare members are squarely Aetna's business), a standard invention-assignment/"work-made-for-hire" clause may vest IP in the employer even on personal devices/time ([Copyright Office Circ. 30](https://copyright.gov/circs/circ30.pdf); [Opticliff side-project guide](https://opticliff.com/legal-issues-consider-startup-side-project-separate-day-job/)). The benefit-loss context makes "relates to employer's business" a live question — **get written sign-off or a clear personal-project carve-out** before public release.
- [ ] **Keep personal and enterprise GitHub strictly separated.** Do not push to a personal account using enterprise SSO/credentials, and do not push enterprise IP to a personal repo. Many orgs use a **Balanced Employee IP Agreement (BEIPA)** model — even there, IP "related to the company's business" grants the company a license ([GitHub BEIPA](https://github.com/github/balanced-employee-ip-agreement)). Ask whether Aetna/CVS has an equivalent.
- [ ] **No internal Aetna data, member lists, plan documents, or non-public benefit data** in this repo — only public source material. (This is already enforced by the zero-PII constraint.)
- [ ] Decide repo visibility deliberately: a public repo of *public* data is fine on the data side, but the **governance/IP question above governs whether you may publish at all**.

---

## 2. Open-source tools & standards

### Standard: OpenReferral HSDS (the backbone schema)
- **Spec:** Human Services Data Specification — current **v3.2.3 (Mar 2026)**, licensed **CC BY-SA 4.0**. ([repo](https://github.com/openreferral/specification), [docs](https://docs.openreferral.org/), [schema reference](https://docs.openreferral.org/en/latest/hsds/schema_reference.html))
- **Core objects:** `organization`, `service`, `location`, `service_at_location` (plus `phone`, `address`, `schedule`, `eligibility`, `accessibility`, `service_area`, `taxonomy_term`). Adopt this directly — it already models eligibility/hours/service-area/contact cleanly and gives you free interoperability with 211 feeds.
- **API protocol:** HSDA / HSDS API spec ([api-specification](https://openreferral.github.io/api-specification/)) — use for the read API shape if you build one.

### Ingest / 211 / HSDS tooling
- **HSDS validators & sample data:** [openreferral/specification](https://github.com/openreferral/specification) ships JSON Schema + `core_tables.csv` for validation. Use the published JSON Schema to validate every ingested record.
- General approach: pull HSDS feeds where a state 211/United Way publishes them; otherwise model `.gov` open data into HSDS objects yourself.

### Geocoding & ZIP→county
- **Census Geocoder API** — free, public-domain US government service; address → lat/long + FIPS (state/county/tract). Primary geocoder. ([Census geocoder FAQ](https://www2.census.gov/geo/pdfs/maps-data/data/FAQ_for_Census_Bureau_Public_Geocoder.pdf))
- **HUD–USPS ZIP Code Crosswalk** (API + quarterly files) — ZIP→county and ZIP→tract, with allocation ratios for ZIPs spanning counties (relevant for Kansas City straddling multiple counties). ([HUD API](https://www.huduser.gov/portal/dataset/uspszip-api.html), [files](https://www.huduser.gov/portal/datasets/usps_crosswalk.html))
- **Census ANSI/FIPS code lists** — canonical county codes for KS/MO. ([Census ANSI/FIPS](https://www.census.gov/library/reference/code-lists/ansi.html))
- Note: matches your stored geo convention (bare city names, MO/KS, one row per city-county pair, Kansas City multi-county) — the HUD crosswalk's allocation ratios are exactly how to enumerate KC's multiple counties.

### Dedup / verification
- **Splink** ([moj-analytical-services/splink](https://github.com/moj-analytical-services/splink)) — probabilistic record linkage, scales on a laptop via DuckDB; best default for deduping orgs/locations across multiple source feeds.
- **Python Record Linkage Toolkit** ([J535D165/recordlinkage](https://github.com/J535D165/recordlinkage)) — modular indexing/compare/classify; good for small/medium directory sizes.
- **dedupe** ([dedupe.io / dedupeio/dedupe](https://github.com/dedupeio/dedupe)) — active-learning fuzzy matching; fine for <10K records (memory-bound above that).
- Curated catalog of options: [J535D165/data-matching-software](https://github.com/J535D165/data-matching-software).

### Verification scaffolding (build, not borrow)
- Every record: `source_url`, `date_checked`, `confidence` (e.g. high = corroborated by 2+ sources incl. one `.gov`/official feed; medium = single official feed; low = single aggregator listing pending re-verify).
- CI guard: JSON-Schema-validate against HSDS **and** reject any field outside the allowed public-org field set (PII tripwire from §1C).

---

## 3. Per-source license summary

| Source | License | Attribution required? | Redistribution allowed? | Notes |
|---|---|---|---|---|
| **OpenReferral HSDS spec** | CC BY-SA 4.0 | Yes | Yes (share-alike on derivatives *of the spec*) | Schema only; your data isn't encumbered by SA. [docs](https://docs.openreferral.org/) |
| **211 HSDS feeds (state 211/United Way)** | Varies per publisher — check each | Usually yes | Usually yes if HSDS-published; **verify per feed** | Strip AIRS taxonomy codes unless licensed |
| **AIRS / 211 LA Taxonomy** | Proprietary, paid license | N/A | **No** | Do NOT embed/redistribute. [AIRS](https://www.airs.org/i4a/pages/index.cfm?pageid=3386) |
| **findhelp / Aunt Bertha listings** | Proprietary "Findhelp Content" | N/A | **No** (ToS prohibits) | Fact-corroboration only, no bulk/re-host. [ToS](https://www.auntbertha.com/legal/terms) |
| **USDA SNAP Retailer Locator** | CC BY 4.0 | **Yes** | Yes | [data.gov](https://catalog.data.gov/dataset/snap-retail-locator) |
| **USDA Food Access Research Atlas** | CC0 (public domain) | No (courtesy credit) | Yes | [data.gov](https://catalog.data.gov/dataset/food-access-research-atlas) |
| **Census Geocoder API** | US Gov public domain | No | Yes | Free, no key |
| **HUD–USPS ZIP Crosswalk** | US Gov public domain | No (courtesy credit) | Yes | API token required (free). [HUD](https://www.huduser.gov/portal/dataset/uspszip-api.html) |
| **Census ANSI/FIPS code lists** | US Gov public domain | No | Yes | [Census](https://www.census.gov/library/reference/code-lists/ansi.html) |
| **State agency open data (KS/MO .gov)** | Varies — typically open/public-record | Check each | Usually yes | Record per-dataset terms in register |

*General rule:* US federal government works are **public domain (17 U.S.C. §105)**; data.gov entries may still carry CC BY/CC0 tags — honor whichever the catalog states.

---

## 4. Risks & how safe-route constraints mitigate them

| Risk | Mitigation (built into constraints) |
|---|---|
| **HIPAA/PHI exposure** | Zero member data ever; schema physically cannot hold PII; CI tripwire rejects member-shaped fields → out of HIPAA scope by construction. |
| **ToS breach / breach-of-contract (findhelp, AIRS)** | Safe-route ranking favors `.gov`/HSDS open feeds; aggregators used only for single-fact corroboration, never bulk export or re-hosting. |
| **Copyright infringement** | Extract non-copyrightable *facts*, re-key prose; do not reproduce documents wholesale; AIRS taxonomy excluded. |
| **Scraping / CFAA / robots.txt violations** | No automated collection from any site that forbids it; robots.txt + ToS checked before any fetch. |
| **Stale/inaccurate referrals harming members** | Mandatory `source_url + date_checked + confidence`; multi-source corroboration for high confidence; periodic re-verification. |
| **Employer IP / personal-vs-enterprise GitHub** | Confirm IP ownership and obtain written carve-off before public release; strict separation of personal/enterprise accounts/credentials; no internal Aetna data in repo. |
| **Attribution failures (license non-compliance)** | Per-source license register + credits page + per-record `source`; CC BY sources get visible attribution. |
| **Multi-county geo errors (e.g., Kansas City)** | HUD crosswalk allocation ratios + Census FIPS enumerate all counties per ZIP/city, matching the one-row-per-city-county convention. |

---

**Open items to resolve before any data collection phase:** (1) written IP/governance sign-off re: Aetna business relatedness; (2) per-feed license confirmation for each KS/MO 211/United Way HSDS source; (3) confirm no AIRS-coded taxonomy is redistributed.

**Relevant project paths:** `/Users/butterhorn/kansas-missouri-ssbci-resources/db/` (apply HSDS schema + PII tripwire here), `/Users/butterhorn/kansas-missouri-ssbci-resources/pipeline/` (ingest/geocode/dedup tooling), `/Users/butterhorn/kansas-missouri-ssbci-resources/docs/` (license register + attribution/credits + HIPAA-not-applicable rationale).
