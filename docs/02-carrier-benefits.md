The folders are empty scaffolding. This is a planning deliverable. I'll write the markdown research document directly as my return value. The task is research synthesis based on public plan knowledge, with explicit verification flags per the constraints.

Here is the deliverable:

---

# KS + MO Medicare Advantage Carriers — SSBCI / Flex / Grocery-Card Benefit Research

**Purpose:** Map what SSBCI-qualifying (chronically ill) MA members in Kansas and Missouri are *losing* effective 1/1/2027, so we can match those losses to replacement community resources.
**Scope of this doc:** Carrier landscape + benefit taxonomy + normalized catalog design. This is PLAN/SCAFFOLD. No live resource records collected.
**CRITICAL CAVEAT:** Benefit names, dollar amounts, covered categories, and which plans even *offer* SSBCI benefits **change every plan year** and vary by **plan ID (H-contract/PBP) and county**. Every value below is **a research hypothesis from public/general knowledge and MUST be verified** against the current-year Summary of Benefits (SB), Evidence of Coverage (EOC), and the CMS Plan Finder before use. Treat all "[VERIFY]" tags as blocking.

> **Regulatory context (verify against CMS):** SSBCI = *Special Supplemental Benefits for the Chronically Ill*, authorized by the CHRONIC Care Act / Bipartisan Budget Act of 2018 and codified at **42 CFR 422.102(f)**. SSBCI benefits (e.g., general groceries, utilities, rent assistance, pet supplies, transportation for non-medical needs) are available only to enrollees who meet the **chronically ill enrollee** definition (one or more complex chronic conditions + high risk of hospitalization + need for intensive care coordination). This is distinct from broad "primarily health-related" supplemental benefits (e.g., standard OTC cards) that any plan member can get. **The 1/1/2027 loss event in scope should be confirmed**: CMS issued guidance tightening SSBCI documentation, the "Flex card"/grocery-card marketing, and primarily-health-related rules (notably the **CY2025 Final Rule** on supplemental-benefit substantiation and the Mid-Year Notice of Unused Supplemental Benefits). Confirm whether the 2027 loss is carrier plan-design exits, a CMS rule change, or both. **[VERIFY — this drives everything]**

---

## 1. Major MA Carriers Operating in Kansas and Missouri

Parent companies and their KS/MO-relevant brands. Footprint (which counties, HMO vs PPO vs D-SNP/C-SNP) **must be verified per plan year** via CMS Plan Finder and state DOI filings.

| # | Parent / Carrier | KS/MO brand(s) commonly seen | Plan types relevant to SSBCI | Notes / [VERIFY] |
|---|---|---|---|---|
| 1 | **UnitedHealth Group** | UnitedHealthcare (UHC), incl. AARP-branded; UHC Dual Complete (D-SNP) | HMO, PPO, **D-SNP, C-SNP** | Largest national MA insurer; strong KC metro + statewide presence. SSBCI most concentrated in D-SNP/C-SNP and chronic-condition plans. |
| 2 | **Humana** | Humana (incl. Humana Gold Plus HMO, Humana USAA co-brand) | HMO, PPO, **D-SNP, C-SNP** | Heavy MA footprint both states; "Healthy Options" allowance card is the marquee SSBCI/flex vehicle. |
| 3 | **CVS Health / Aetna** | Aetna Medicare; Aetna Medicare Dual (D-SNP) | HMO, PPO, **D-SNP, C-SNP** | Aetna's "Extra Benefits Card" / "Medicare Payment Card" used for OTC + (in SSBCI plans) groceries/utilities. *(Note: user's auto-memory references Aetna Medicare work — cross-link if relevant.)* |
| 4 | **Centene** | **Wellcare** (KS + MO), **Ascension Complete** (where applicable) | HMO, PPO, **D-SNP** | Wellcare is a major value/dual brand in both states; "Flex Card"/spendables common. |
| 5 | **Elevance Health (Anthem)** | **Anthem Blue Cross Blue Shield** (MO Anthem footprint), Anthem MediBlue | HMO, PPO, **D-SNP** | Anthem operates BCBS in Missouri (most counties). "Benefits Mastercard / Essential Extras." |
| 6 | **Blue Cross and Blue Shield of Kansas City (Blue KC)** | **Blue KC Medicare Advantage** | HMO, PPO | Regional Blue plan for the **bistate KC metro** (covers select KS + MO counties). Independent of Anthem. **[VERIFY county list]** |
| 7 | **Blue Cross and Blue Shield of Kansas (BCBSKS)** | BCBSKS Medicare Advantage / Blue Medicare Advantage | HMO, PPO | Kansas statewide Blue (outside the KC-metro Blue KC area). Independent licensee. |
| 8 | **Cigna Healthcare** | Cigna Medicare (Cigna HealthSpring legacy in MO) | HMO, PPO | Footprint varies by year; historically stronger in MO metros. **[VERIFY current counties]** |
| 9 | **Essence Healthcare** | Essence Healthcare (St. Louis-based) | HMO | Regional MO insurer, strong **St. Louis** metro. **[VERIFY]** |
| 10 | **Cox HealthPlans / Medicare** | (SW Missouri / Springfield area) | HMO | Regional; **[VERIFY whether still offering MA in plan year]** |
| 11 | **Devoted Health** | Devoted Health | HMO/PPO | Growth-stage national insurer expanding into MO/KS metros. **[VERIFY footprint]** |
| 12 | **Clover Health** | Clover Health | PPO | Historically present in some MO counties. **[VERIFY]** |
| 13 | **Imperial / Alignment / Zing / other entrants** | varies | varies | Smaller/newer entrants change yearly. **[VERIFY each plan year on Plan Finder]** |

**How to confirm the canonical list (do this before any data work):**
- **CMS Medicare Plan Finder** (medicare.gov) — filter by KS and MO ZIPs/counties; export plan list (H-contract + PBP). *Open/public.*
- **CMS Monthly MA Enrollment & Landscape files** (cms.gov public-use files) — authoritative carrier/contract list by county. *Open data — best single source.*
- **Kansas Insurance Department** and **Missouri Department of Commerce & Insurance** — licensed-carrier verification.

---

## 2. Per-Carrier SSBCI / Flex / Grocery / OTC Benefit Profiles

**Read this first:** The benefit names below are the **marketing names carriers have historically used**; they are reused loosely and reassigned year to year. The same card is often used for **multiple wallets** (OTC, groceries, utilities) with category-level spending rules. Coverage of **rent, pet food, and gas/transport is almost always SSBCI-gated** (chronically-ill only) and is the *most likely* to be cut. **Every cell is [VERIFY] against current SB/EOC.**

### 2.1 UnitedHealthcare
- **Common benefit name(s):** "**UCard**" (the unified member card/wallet); credits often labeled "**Food, OTC & Utilities credit**," "Healthy Food Benefit," "Credit allowance."
- **Typical coverage (SSBCI / D-SNP/C-SNP plans):** groceries (healthy-food catalog or in-store), OTC items, **utility bill** payments; some plans add transportation. **Rent/pet food: plan-specific [VERIFY].**
- **Public cite to pull:** UHC plan-year **Summary of Benefits** + "UCard" benefit pages on uhc.com; D-SNP SB PDFs per county. **[VERIFY]**

### 2.2 Humana
- **Common benefit name(s):** "**Healthy Options Allowance**" (flagship SSBCI/flex card); legacy "Healthy Foods Card," "Spending Allowance."
- **Typical coverage:** groceries, OTC, **utilities, rent**, and in some chronic plans **pet care/transportation** — Humana's Healthy Options has historically been one of the broadest. **[VERIFY categories + $/month]**
- **Public cite:** Humana.com "Healthy Options Allowance" benefit page + plan SB PDFs. **[VERIFY]**

### 2.3 Aetna (CVS Health)
- **Common benefit name(s):** "**Extra Benefits Card**," "**Medicare Payment Card**," "Healthy Foods Card."
- **Typical coverage:** OTC + (SSBCI plans) **healthy groceries, utilities**; CVS-store OTC integration. **[VERIFY rent/pet/transport]**
- **Public cite:** aetnamedicare.com plan pages + SB PDFs. **[VERIFY]**

### 2.4 Wellcare (Centene)
- **Common benefit name(s):** "**Flex Card**," "**Spendables**," "Healthy Foods Card," OTC allowance.
- **Typical coverage:** OTC, groceries, **utilities, dental/vision/hearing cost-share**; SSBCI plans may add rent/transport. **[VERIFY]**
- **Public cite:** wellcare.com / Centene plan SB PDFs by state. **[VERIFY]**

### 2.5 Anthem BCBS (Elevance) — Missouri
- **Common benefit name(s):** "**Benefits Mastercard**," "**Essential Extras**," "Healthy Groceries," "Utility/Grocery allowance."
- **Typical coverage:** "Essential Extras" lets member pick categories (e.g., groceries, utilities, transportation, pet care, assistive devices) — **menu model**. SSBCI-gated categories likely. **[VERIFY menu + eligibility]**
- **Public cite:** anthem.com Medicare plan pages (MO) + SB PDFs. **[VERIFY]**

### 2.6 Blue KC (BCBS of Kansas City) — bistate KC metro
- **Common benefit name(s):** OTC/flex allowance, "Healthy Benefits+" style card (vendor-administered). **[VERIFY exact name]**
- **Typical coverage:** OTC, possibly healthy groceries on select plans. SSBCI breadth **[VERIFY]**.
- **Public cite:** bluekc.com Medicare plan pages + SB. **[VERIFY]**

### 2.7 BCBS of Kansas (BCBSKS)
- **Common benefit name(s):** OTC allowance / flex card. **[VERIFY]**
- **Typical coverage:** OTC; grocery/utility breadth **[VERIFY per plan]**.
- **Public cite:** bcbsks.com Medicare pages + SB. **[VERIFY]**

### 2.8 Cigna
- **Common benefit name(s):** "**Cigna Healthy Today Card**" / flex allowance.
- **Typical coverage:** OTC, groceries, utilities, some transportation on SSBCI plans. **[VERIFY]**
- **Public cite:** cigna.com Medicare plan pages + SB. **[VERIFY]**

### 2.9 Regional MO insurers (Essence, Cox, others)
- **Common benefit name(s):** OTC allowance; flex/grocery varies. **[VERIFY each]**
- **Public cite:** carrier Medicare plan pages + SB PDFs. **[VERIFY]**

### 2.10 Devoted / Clover / new entrants
- **Common benefit name(s):** "Devoted Dollars" / spending card; vendor-administered flex cards. **[VERIFY]**
- **Public cite:** carrier plan pages + SB. **[VERIFY]**

**Benefit-category cheat sheet (what to look for in each SB), mapped to our replacement-resource buckets:**

| Benefit category in SB | Our replacement resource bucket | Typical SSBCI-gated? |
|---|---|---|
| Healthy food / grocery allowance, "Healthy Foods Card" | **Food** (pantries, 211 food, USDA/SNAP, congregate meals) | Often (general groceries = SSBCI); healthy-food can be primarily-health-related |
| OTC allowance | (Prescription/health-aisle adjacent) | Usually NOT SSBCI (broad) |
| Utility / "energy" allowance | **Utility assistance** (LIHEAP, local) | Yes |
| Rent / housing allowance | **Rent / housing assistance** | Yes |
| Pet food / pet care | **Pet-food** resources | Yes |
| Transportation / gas (non-medical) | **Gas / transport** | Yes (non-medical transport = SSBCI) |
| Prescription cost help / Part D extras | **Prescription assistance** | Varies |

---

## 3. Normalized Catalog Plan — Fields to Capture Per Carrier Benefit

Goal: a structured record per **(carrier × plan × benefit × plan-year × county-set)** that lets us compute "**member is losing X**" → "**community resource Y replaces it**." Two linked tables.

### 3.1 Table A — `carrier_benefit` (the thing members lose)

| Field | Type | Description | Required |
|---|---|---|---|
| `benefit_id` | uuid/pk | Stable internal key | yes |
| `parent_company` | string | e.g., "Centene" | yes |
| `carrier_brand` | string | e.g., "Wellcare" | yes |
| `plan_name` | string | Marketed plan name | yes |
| `cms_contract_id` | string | H-contract (e.g., H1234) | yes [VERIFY] |
| `cms_pbp_id` | string | Plan Benefit Package # | yes [VERIFY] |
| `plan_type` | enum | HMO/PPO/D-SNP/C-SNP/MMP | yes |
| `plan_year` | int | e.g., 2026 / 2027 | yes |
| `state` | enum | KS / MO / BOTH | yes |
| `county_scope` | array<string> | FIPS or county names covered | yes [VERIFY] |
| `benefit_marketing_name` | string | e.g., "Healthy Options Allowance" | yes |
| `benefit_card_vendor` | string | e.g., NationsBenefits / Incomm / OTCHS | optional |
| `benefit_categories` | array<enum> | {groceries, otc, utilities, rent, pet_food, transport_nonmedical, prescription, dental, vision, hearing, other} | yes |
| `ssbci_flag` | bool | Is this an SSBCI (chronically-ill-only) benefit? | yes |
| `eligibility_conditions` | text | Qualifying chronic conditions / dual status | yes [VERIFY] |
| `allowance_amount` | money | $ per period | yes [VERIFY] |
| `allowance_period` | enum | monthly/quarterly/annual | yes |
| `allowance_rollover` | bool | Unused rolls over? | optional |
| `redemption_channels` | array | in-store, online catalog, bill-pay, card swipe | optional |
| `ends_effective_date` | date | When benefit ends (target: 2027-01-01) | yes |
| `loss_summary` | text | Plain-language "what you're losing" for member-facing matching | yes |
| `source_url` | url | Public SB/EOC/plan page | **yes** |
| `source_doc_type` | enum | SB / EOC / plan-page / CMS-PlanFinder / landscape-file | yes |
| `date_checked` | date | When verified | **yes** |
| `confidence` | enum | high / medium / low / unverified | **yes** |
| `license_attribution` | string | Source license/terms (e.g., CMS public-domain; carrier ToS note) | yes |
| `extracted_by` | enum | human / automated | yes |
| `notes` | text | Caveats, ambiguities | optional |

### 3.2 Table B — `benefit_to_resource_map` (the bridge to community replacements)

| Field | Type | Description |
|---|---|---|
| `map_id` | uuid/pk | — |
| `benefit_id` | fk → carrier_benefit | The lost benefit |
| `resource_bucket` | enum | food / utility / rent / pet_food / gas_transport / prescription / housing |
| `geography_key` | string | County/ZIP to constrain resource search |
| `priority` | int | Match strength for member triage |
| `notes` | text | e.g., "grocery allowance → LIHEAP won't help; route to pantry + SNAP" |

> Resource-side records (the actual pantries/LIHEAP offices/etc.) live in a **separate `resource` table** populated **only** via the SAFE ROUTE sources (211/United Way, OpenReferral HSDS, HHS/USDA/state open data, findhelp/Aunt Bertha public listings, .gov). That table is out of scope for *this* deliverable but `benefit_to_resource_map.resource_bucket` + `geography_key` are the join keys.

### 3.3 Design notes / rules
- **Grain = plan-year × PBP × benefit.** Never store a benefit without its plan-year and PBP — values are not stable across years or plans.
- **CMS public files first.** Use CMS landscape/enrollment/Plan Finder (public domain) to enumerate plans; use carrier SB/EOC PDFs only to *extract facts* (amounts, categories), never to reproduce the documents.
- **Every row carries `source_url` + `date_checked` + `confidence` + `license_attribution`** (hard constraint).
- **Confidence ladder:** `high` = pulled from current-year official SB/EOC; `medium` = carrier marketing page; `low` = prior-year doc or secondary source; `unverified` = hypothesis (everything in §1–§2 above).
- **SSBCI gate is the key filter:** the members in scope are chronically-ill SSBCI recipients, so prioritize `ssbci_flag = true` benefits (groceries-general, utilities, rent, pet, non-medical transport) — those are what's being lost and what community resources must backfill.

---

## Verification Checklist (must complete before any record is trusted)
1. [VERIFY] Confirm the **1/1/2027 benefit-loss trigger** (CMS rule vs. carrier exits vs. both).
2. [VERIFY] Pull current **CMS MA Landscape / enrollment file** for KS + MO → authoritative carrier/contract list (replaces §1 guesses).
3. [VERIFY] For each in-scope plan, pull the **current-year SB + EOC** → fill `benefit_*` fields and `confidence=high`.
4. [VERIFY] Capture **license/attribution** per source (CMS = public domain; carrier docs = fact-extraction only).
5. [VERIFY] Confirm **county scope** per plan (esp. bistate Blue KC; KS BCBSKS vs Blue KC split).

**Relevant project path:** `/Users/butterhorn/kansas-missouri-ssbci-resources/` (scaffold dirs `data/`, `docs/`, `pipeline/` are empty; this research doc is the planning artifact for §3's schema and the carrier-source catalog).

**Bottom line:** §1 carrier list is reliable at the parent-company level but **footprint/plan availability is [VERIFY]**; §2 benefit names are **directional and must be confirmed against current SB/EOC**; §3 schema is ready to implement and is the load-bearing deliverable for mapping lost benefits to community resources.
