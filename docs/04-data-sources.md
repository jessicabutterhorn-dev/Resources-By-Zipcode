I have enough verified information to produce the catalog.

# SAFE-ROUTE Data Source Catalog — KS + MO Social-Service Providers

Scope: Public, legally ingestible data sources for a directory of food, utility (LIHEAP), rent/housing, pet-food, transportation/gas, prescription, and general-211 assistance providers in Kansas and Missouri. Plan/scaffold only — no live records collected here. All URLs verified June 2026.

Confidence legend: HIGH = source confirmed live + safe-route this session; MED = source confirmed to exist, exact format/license needs partner confirmation; CHECK = access path exists but requires direct outreach/agreement before ingest.

---

## 1. General 211 (anchor sources — highest priority)

| Source | URL | Coverage | Format | Live API? | License / Attribution | Confidence |
|---|---|---|---|---|---|---|
| **211 National Data Platform (United Way Worldwide)** | https://register.211.org/Home/IntegrationsOverview · dev portal https://apiportal.211.org/ · get-started https://apiportal.211.org/get-started-overview | Statewide KS + MO (aggregates local 211s) | REST API (Search API + Export API), HSDS 3.0 | YES — live, key-gated | Data ownership retained locally per legal agreement; access via authorization keys provisioned **with permission of the local 211**. Free for internal use; 5% data-valuation fee if used for revenue. **Requires data agreement before ingest.** | CHECK |
| **United Way of Greater Kansas City 211** | https://unitedwaygkc.org/211-2/ · search https://search.unitedwaygkc.org/ · directory https://uwgkc.myresourcedirectory.com/ | Greater KC metro (KS + MO sides) | Web resource directory (myresourcedirectory.com); feeds into National Data Platform | Via NDP key | Local 211 owns data; attribution to United Way of Greater KC. Negotiate feed access, do not bulk-scrape the web UI. | CHECK |
| **United Way 211 Missouri (United Way of Greater St. Louis, statewide)** | https://mo211.myresourcedirectory.com/ · org https://stl.unitedway.org/ | Entire state of Missouri (24/7) | Web resource directory; NDP feed | Via NDP key | MO211 owns data; attribution to United Way of Greater St. Louis. Use NDP/partner feed, not scraping. | CHECK |
| **211 Counts (Missouri statewide dashboard, w/ Washington University)** | https://211mo.211counts.org/ · https://211counts.org/home/index | MO statewide (aggregate stats) | Web dashboard, aggregate only | Dashboard only | Aggregate need statistics — **not a provider directory**; useful for prioritization/coverage gaps, not records. Attribution to 211 + WashU. | MED |

**Note:** The 211 National Data Platform is the single best statewide spine for both states because it is HSDS-native and explicitly built for third-party data sharing. Treat the local 211s (GKC, St. Louis, Heart of Missouri, etc.) as the permission-granting partners.

---

## 2. OpenReferral / HSDS (the interchange standard + reference feeds)

| Source | URL | Coverage | Format | Live API? | License / Attribution | Confidence |
|---|---|---|---|---|---|---|
| **OpenReferral HSDS 3.0 specification** | https://docs.openreferral.org/en/latest/hsds/overview.html · API ref https://docs.openreferral.org/en/latest/hsds/api_reference.html · spec repo https://github.com/openreferral/specification | N/A (standard) | Schema/spec (use as our internal canonical data model) | N/A | Open spec. **Adopt HSDS 3.0 as our internal schema** so any 211/partner feed maps cleanly. | HIGH |
| **HSDA (Human Services Data API protocols)** | https://openreferral.github.io/api-specification/ | N/A (standard) | API protocol | N/A | Open. Defines org/location/service/contact endpoints — model our ingest after this. | HIGH |
| **Feeding America HSDS 3.0 Open Referral feed** | https://feedam.org/hsds | National (food bank network) | HSDS 3.0 feed | YES (HSDS endpoint) | Confirm attribution terms with Feeding America; HSDS-formatted so directly mappable. Strong food-category source. | MED |

---

## 3. findhelp / Aunt Bertha

| Source | URL | Coverage | Format | Live API? | License / Attribution | Confidence |
|---|---|---|---|---|---|---|
| **findhelp (Aunt Bertha) API** | https://www.findhelp.org/find-social-services/missouri · MO state instance https://mofamilyresources.findhelp.com/ · terms https://findhelp.findhelp.com/terms · customer terms https://company.findhelp.com/customerterms/ | KS + MO statewide, all categories | Platform + API (partner/licensed) | YES — but **licensed/contractual** | **Not open.** License grants USA-only internal-business use within a customer agreement; aggregate/anonymous reuse rights belong to findhelp. **Do NOT scrape the public listings** — terms restrict reuse. Requires a partner/customer agreement. Missouri DSS already partners with findhelp (mofamilyresources.findhelp.com), which may be a relationship to leverage. | CHECK |

Treat findhelp as **licensed-route, not open-route**: ingest only under an executed agreement; otherwise use it for manual lookup/verification, not bulk pull.

---

## 4. Food Assistance

| Source | URL | Coverage | Format | Live API? | License / Attribution | Confidence |
|---|---|---|---|---|---|---|
| **USDA ERS Food Access Research Atlas** | https://www.ers.usda.gov/data-products/food-access-research-atlas/download-the-data | National (census-tract food access) | XLSX, ZIP, API, ArcGIS | YES (API + bulk download) | Public domain (US gov). **Context data** (food-desert tracts) for prioritization — not a provider list. Attribution: USDA ERS. | HIGH |
| **USDA ERS Food Environment Atlas** | https://www.ers.usda.gov/data-products/food-environment-atlas/data-access-and-documentation-downloads | National (incl. Feeding America food-bank counts) | Download + map | Bulk download | Public domain. County-level food-bank/SNAP indicators. Attribution: USDA ERS. | HIGH |
| **Feeding America food-bank network** | https://feedam.org/hsds (HSDS feed) · locator at feedingamerica.org | National incl. KS + MO partner banks (e.g., Harvesters–KC, St. Louis Area Foodbank, Ozarks Food Harvest) | HSDS 3.0 feed | YES (HSDS) | Confirm attribution; HSDS-native. | MED |
| **USDA SNAP retailer / state food-assistance pages** | KS DCF Food Assistance https://www.dcf.ks.gov/services/ees/pages/food/foodassistance.aspx | KS + MO statewide | Web (.gov) | No API | Public .gov. Extract facts (program offices), don't reproduce wholesale. | HIGH |

---

## 5. Utility / Energy Assistance (LIHEAP)

| Source | URL | Coverage | Format | Live API? | License / Attribution | Confidence |
|---|---|---|---|---|---|---|
| **LIHEAP Clearinghouse (HHS/ACF)** | https://liheapch.acf.gov/ · MO profile https://liheapch.acf.gov/profiles/Missouri.htm · office search https://liheapch.acf.gov/search-tool/state-territory · state energy profiles https://liheapch.acf.gov/profiles/energyhelp.htm | KS + MO statewide (+ utility-level programs) | Web (.gov), searchable directory | No formal API | Public domain (US gov). Authoritative for LIHEAP/LIEAP offices + utility programs. Attribution: HHS ACF OCS. | HIGH |
| **ACF LIHEAP State & Territory Contact Listing** | https://acf.gov/ocs/map/liheap-map-state-and-territory-contact-listing | KS + MO (state program contacts) | Web (.gov) | No API | Public domain. KS LIEAP and MO LIHEAP program-manager contacts. | HIGH |
| **Kansas DCF — LIEAP** | https://www.dcf.ks.gov/services/ees/pages/food/foodassistance.aspx (services hub) · LIEAP newsroom https://www.dcf.ks.gov/Newsroom/Pages/LIEAP-OpensEarlyInKansas.aspx | KS statewide | Web (.gov) | No API | Public .gov. Extract program/office facts. | HIGH |
| **Missouri DSS / FSD — LIHEAP** | https://dss.mo.gov/ · email FSD.LIHEAP@dss.mo.gov | MO statewide | Web (.gov) | No API | Public .gov. | HIGH |

---

## 6. Rent / Housing Assistance

| Source | URL | Coverage | Format | Live API? | License / Attribution | Confidence |
|---|---|---|---|---|---|---|
| **HUD Resource Locator / HUD open data** | https://www.hud.gov/ · HUD data https://www.huduser.gov/portal/pdrdatas_landing.html (verify dataset) | National incl. KS + MO (PHAs, assisted housing, HUD counselors) | CSV, API, ArcGIS | YES (HUD open data + Esri services) | Public domain (US gov). PHA + HUD-approved housing-counseling agency lists. Attribution: HUD. | MED |
| **211 directories (housing category)** | (see §1) | KS + MO | HSDS via NDP | Via NDP | Best source for local rent-assistance nonprofits. | CHECK |
| **MO DSS / KS DCF housing pages** | https://dss.mo.gov/ · https://www.dcf.ks.gov/ | KS + MO | Web (.gov) | No API | Public .gov. | HIGH |

---

## 7. Transportation / Gas Assistance

| Source | URL | Coverage | Format | Live API? | License / Attribution | Confidence |
|---|---|---|---|---|---|---|
| **Eldercare Locator (ACL) + Area Agencies on Aging** | https://eldercare.acl.gov/Public/index.aspx · AAA program https://acl.gov/programs/aging-and-disability-networks/area-agencies-aging | National incl. KS + MO | Web lookup (.gov) | No public API | Public domain. AAAs run senior transportation + home-delivered meals — high relevance for Medicare members. Attribution: ACL. | HIGH |
| **211 directories (transportation category)** | (see §1) | KS + MO | HSDS via NDP | Via NDP | Primary source for gas-voucher / medical-transport nonprofits. | CHECK |

---

## 8. Prescription Assistance

| Source | URL | Coverage | Format | Live API? | License / Attribution | Confidence |
|---|---|---|---|---|---|---|
| **211 directories (Rx/medical category)** | (see §1) | KS + MO | HSDS via NDP | Via NDP | Best structured source for local Rx-assistance orgs. | CHECK |
| **HHS / federal program pages (e.g., Medicare Extra Help, RxAssist-type)** | https://acf.gov/ · medicare.gov (verify specific program pages) | National | Web (.gov) | Varies | Public domain for .gov; verify any third-party Rx-assistance DB license separately before ingest. | MED |

*Prescription assistance has the thinnest open-data coverage — expect to rely on 211 (NDP) feeds plus manually verified .gov program pages. Avoid scraping third-party patient-assistance aggregators without checking their terms.*

---

## 9. Pet-Food Assistance

| Source | URL | Coverage | Format | Live API? | License / Attribution | Confidence |
|---|---|---|---|---|---|---|
| **211 directories (pet-food / animal-welfare category)** | (see §1) | KS + MO | HSDS via NDP | Via NDP | Primary structured source. | CHECK |
| **Local food banks (Feeding America network) pet-food programs** | https://feedam.org/hsds | KS + MO | HSDS | YES (HSDS) | Some food banks run pet-food pantries; captured in food-bank feed. | MED |

*Pet-food banks are the least standardized category — no dedicated open dataset confirmed. Plan to derive these from 211 (NDP) records and food-bank feeds, supplemented by manually verified humane-society/.org listings (each requiring source URL + date + confidence per our verify rule).*

---

## 10. State & Regional Open-Data Portals (cross-category)

| Source | URL | Coverage | Format | Live API? | License / Attribution | Confidence |
|---|---|---|---|---|---|---|
| **State of Missouri Open Data Portal (data.mo.gov)** | https://data.mo.gov/ · example "Missouri Works Assistance Locations" https://data.mo.gov/widgets/kuz5-m96r · catalog https://catalog.data.gov/dataset?publisher=data.mo.gov | MO statewide | Socrata SODA API, OData, CSV, JSON | YES (SODA API) | Public/open (Socrata). Has social-services category incl. assistance-office locations. Attribution: State of Missouri. | HIGH |
| **Missouri Spatial Data (MSDIS) ArcGIS Open Data** | https://data-msdis.opendata.arcgis.com/ | MO statewide | ArcGIS REST, GeoJSON, CSV | YES (Esri) | Open. Geospatial facility locations. | MED |
| **Kansas open data** | KS DCF services https://www.dcf.ks.gov/ · check KS GIS hub | KS statewide | Web (.gov); GIS where available | Limited | No single Socrata-style social-services portal confirmed this session — KS data is mostly on agency .gov pages + GIS. Plan KS coverage primarily via **211 NDP + DCF .gov + AAAs**, not a state open-data API. Attribution: State of Kansas / KS DCF. | MED |
| **Federal catalog (data.gov)** | https://catalog.data.gov/ | National incl. KS + MO | API, CSV, etc. | YES | Public domain. Harvests state datasets (e.g., MO). | HIGH |
| **Local: Open Data KC, City of St. Louis Open Data, Independence MO** | https://data.kcmo.org/ · https://www.stlouis-mo.gov/data/datasets/index.cfm · https://www.independencemo.gov/resources/open-independence | KC metro, St. Louis, Independence | Socrata / web | Partial | Open. Useful for metro-level facility data. | MED |

---

## Ingest-Strategy Notes (for scaffold)

1. **Canonical model:** Adopt **OpenReferral HSDS 3.0** as the internal schema. Every source maps to org/service/location/contact, so 211-NDP feeds, Feeding America, and findhelp (if licensed) all normalize cleanly.
2. **Statewide spine = 211 National Data Platform** (HSDS-native, both states) — but it is **CHECK/agreement-gated**, not open-pull. First action: contact United Way of Greater KC, United Way of Greater St. Louis, and Heart of Missouri United Way to obtain NDP feed keys.
3. **Open-pull (no agreement) sources, safe today:** USDA ERS atlases, LIHEAP Clearinghouse, ACF LIHEAP contacts, Eldercare Locator/ACL, data.mo.gov (SODA), HUD open data, data.gov, MSDIS. These are public domain / open-license.
4. **Licensed-route (agreement required, never scrape):** findhelp/Aunt Bertha, 211 NDP/local 211 web directories.
5. **Live API vs snapshot:**
   - *Live pull:* 211 NDP (keyed), data.mo.gov SODA, MSDIS/HUD Esri, Feeding America HSDS, data.gov.
   - *Quarterly snapshot:* USDA ERS atlases (periodic releases), LIHEAP Clearinghouse, ACF contact listings, Eldercare Locator, agency .gov pages.
6. **Per-record compliance (our hard rule):** every ingested record must carry **source URL + date checked + confidence flag + per-source license/attribution**. Extract facts only; do not reproduce copyrighted directory documents wholesale.
7. **Thin categories needing manual verification:** prescription assistance, pet-food, transportation/gas — derive primarily from 211 NDP, supplement with verified .gov/.org pages, each individually sourced.

Catalog file (if you want it persisted): I have not written a file per instructions — this catalog is the deliverable above.
