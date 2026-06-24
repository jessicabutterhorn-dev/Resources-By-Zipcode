## Executive Overview — KS+MO SSBCI Benefit-Loss Resource Directory (Plan + Scaffold)

### What members lose on 1/1/2027
The CY2027 MA Final Rule (CMS-4208-F, 91 FR 17384, published 4/6/2026, applicable to coverage 1/1/2027) tightens **SSBCI** (Special Supplemental Benefits for the Chronically Ill) administration under 42 CFR 422.102: objective eligibility (no self-attestation), public posting of plan criteria, real-time point-of-sale card verification locked to plan-approved items, year-locked balances, and removal of the mid-year unused-benefit reminder. Net effect for KS+MO Medicare members: many lose or see sharply narrowed **grocery/produce cards, utility/rent flex dollars, pet-food allowances, non-medical transportation/gas, and OTC flexibility** — either by failing re-qualification or because whole plans drop these benefits. The affected population is low-income, chronically ill, fixed-income seniors least able to absorb the cut.

### What we backfill
A directory of **public** social-service providers across 7 need buckets (food, utility, rent, pet_food, gas_transport, prescription, housing/navigation) that replace the lost benefits, organized so a member can enter a ZIP and see both "what you're losing" and "verified local help."

### Architecture (stack locked)
- **SQLite source of truth** modeled on **OpenReferral HSDS** (organization/service/location/service_at_location + phone/schedule/eligibility/service_area/taxonomy), extended with: (a) a **geography spine** (county/zone/zip_county/city_county) mapping **ZIP -> county -> 1 of 6 collection zones**, HUD-crosswalk-aware for multi-county Kansas City; (b) a **carrier_benefit** layer (grain = plan-year x PBP x benefit) plus `benefit_category` bridging each lost benefit to a resource_bucket; (c) **provenance/verification on every record** via a `source` register (license/attribution/access-route) and `record_provenance` (source_url + date_checked + confidence, multi-source corroboration); (d) `refresh_log` for reproducible quarterly runs.
- **Static HTML + sql.js** front-end: DB ships as a static asset, runs entirely in-browser (no server, no data leaves the device), print-friendly for navigators and members. ZIP -> losses + grouped resource cards, each card showing its confidence + source + date.
- **Reproducible quarterly pipeline**: ingest (safe-route, robots/ToS-gated) -> normalize to HSDS + strip AIRS codes -> geocode (Census + HUD crosswalk) -> dedup (Splink) -> verify (confidence ladder + PII tripwire) -> load SQLite -> rebuild front-end. Live-pull vs snapshot decided per source; every run logged and reproducible from snapshots + git commit.

### Compliance posture (built in, not bolted on)
- **HIPAA out of scope by construction**: schema offers no field capable of holding member/PII data; a CI PII-tripwire rejects member-shaped fields.
- **Safe-route only**: .gov/open feeds first, 211/HSDS next, findhelp/aggregators for single-fact corroboration only — never bulk scrape; robots.txt + ToS checked before any fetch; AIRS taxonomy never redistributed.
- **Provenance everywhere**: per-source license register + per-record source_url/date_checked/confidence; credits page auto-generated for CC BY / share-alike attribution requirements.

### Artifacts delivered here
1. `schema_sql` — complete SQLite DDL (HSDS core + geography/zone spine + carrier_benefit layer + provenance + refresh_log + front-end views).
2. `frontend_plan_md` — static HTML/sql.js spec with print CSS, hosting options, index.html sketch.
3. `pipeline_plan_md` — quarterly refresh pipeline, live-vs-snapshot per source, folder layout, CI guards.
4. `collector_prompt_md` — reusable, zone-parameterized collector prompt enforcing safe-route + verification.

### Next steps (sequenced)
1. Land `db/schema.sql`; load geography reference tables from the canonical `zones.json` + HUD/Census files; run the zone validator (105 KS + 115 MO incl. St. Louis City).
2. Write `pipeline/config/sources.yaml` from the DATA SOURCES catalog (url/license/access_route/refresh_mode per source).
3. Build the open-route connectors first (USDA ERS, LIHEAP Clearinghouse, ACL/Eldercare, data.mo.gov, HUD ZIP, Census geocoder) — these need no agreements.
4. Initiate **211 NDP data agreements** (UW Greater KC, UW Greater St. Louis, Heart of Missouri) — the statewide HSDS spine is agreement-gated.
5. Pull CMS MA Landscape/enrollment files to replace the carrier-list hypotheses; fill carrier_benefit from current-year SB/EOC.
6. Stand up the static front-end against a seeded DB; wire CI (HSDS validation, PII tripwire, provenance assertion, zone validator).

### Open questions for Jessica (blocking before any public release / data collection)
1. **IP/governance sign-off**: The 1/1/2027 benefit-loss context squarely relates to Aetna/CVS business (Medicare members). Get written sign-off or a clear personal-project carve-out before any public repo, and keep personal vs enterprise GitHub strictly separated. Decide repo visibility deliberately.
2. **Confirm the loss trigger**: Validate that the 2027 event in scope is the CMS rule tightening (vs. carrier plan exits vs. both) so loss_summary copy is accurate. (Brief confirms CMS-4208-F; confirm any Aetna-specific plan-design exits.)
3. **211 NDP licensing**: Confirm we can obtain feed keys + redistribution terms from each local 211; without them the statewide spine falls back to .gov + Feeding America + manual verification.
4. **findhelp relationship**: MO DSS already partners with findhelp — leverage as licensed route, or restrict to manual single-fact corroboration? Confirm before any automated use.
5. **Carrier scope**: Which carriers/plans are in-scope for the loss mapping (all KS+MO MA, or Aetna-focused)? Drives how much carrier_benefit data to collect.
6. **Population recompute**: Per-zone populations are 2020-Census estimates; recompute from KLRD (KS) / MERIC (MO) before final workload balancing if zone sizing matters operationally.

All artifacts are plan/scaffold only — no live resource records collected, no member data, consistent with the project's hard constraints.
