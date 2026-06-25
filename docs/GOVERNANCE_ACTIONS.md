# Governance & Data-Agreement Actions

These are the **non-code** steps that unlock the big gated sources and clear the
path to sharing the tool. Code can't do these — they're sign-offs and outreach.
Ranked by leverage.

---

## 0. IP / governance sign-off  ⚠ GATES EVERYTHING

**Why first:** the benefit-loss context is squarely Aetna/CVS business (Medicare
members). Before any public release — and before deciding personal vs. enterprise
GitHub — get written confirmation of ownership / a clear personal-project carve-out.

- **Owner:** Jessica + manager / Aetna legal or compliance
- **Ask:** "Is this an Aetna work product? If so, move it to enterprise GitHub +
  governance. If a personal community project, get a written carve-out."
- **Until resolved:** keep the repo private; do not push to a personal account with
  enterprise credentials. The tool runs fully offline (`file://`), so it can be
  demoed without hosting.
- **Unblocks:** public/hosted deployment, GitHub Pages, sharing beyond the team.

---

## 1. 211 National Data Platform — the statewide directory spine  ⭐ HIGHEST DATA LEVERAGE

**What it unlocks:** one HSDS-native feed covering **food, utility, rent, health,
and more across both states** — far more depth than the per-org connectors. This
is the single biggest data win.

- **Status:** agreement-gated (not open pull). Free for internal use; ~5%
  data-valuation fee only if used to generate revenue.
- **Who to contact (the permission-granting local 211s):**
  - **United Way of Greater Kansas City 211** — search.unitedwaygkc.org (zone 1)
  - **United Way of Greater St. Louis 211** — mo211.myresourcedirectory.com (zones 2–5 MO)
  - **Heart of Missouri United Way 211** — uwheartmo.org (zone 3, mid-MO)
  - **United Ways of Kansas / 211 Kansas** — 211kansas.org (KS statewide)
  - Dev portal once approved: apiportal.211.org
- **Ask:** "We're a nonprofit-facing Medicare-member resource directory (no member
  data, no resale). May we get an NDP HSDS feed key + redistribution terms?"
- **Constraint:** attribution required ("Data provided by local United Way 211").
  Already modeled in `sources.yaml` (211-ndp, enabled=false until keys arrive).

---

## 2. Feeding America HSDS feed — all food banks + pantries  ⭐ FOOD AT SCALE

**What it unlocks:** every network food bank and partner pantry across all 6 zones
in one structured feed — replaces building a fragile connector per food bank
(Harvesters/KFB were WP-widget dead ends).

- **Source:** feedam.org/hsds (HSDS 3.0). Agreement/attribution-gated.
- **Who:** Feeding America national data team (via the regional food banks:
  Harvesters–KC, St. Louis Area Foodbank, Ozarks Food Harvest, Kansas Food Bank,
  Second Harvest–St. Joseph — see `data/zone_food_sources.json`).
- **Ask:** "Can we obtain the HSDS feed + attribution terms for KS+MO partner
  agencies for a nonprofit member-resource directory?"
- **Constraint:** confirm attribution + reuse terms before bulk load. Modeled in
  `sources.yaml` (feeding-america-hsds, enabled=false).

---

## 3. findhelp / Aunt Bertha — leverage the MO DSS partnership

- **Source:** findhelp (proprietary, licensed; never scrape). MO DSS already
  partners (mofamilyresources.findhelp.com).
- **Ask:** "Can we ingest under MO DSS's existing findhelp relationship, or get a
  partner/customer agreement?" If not, use it only for manual single-fact
  verification — never bulk.

---

## Sequence

1. **IP sign-off** (blocks public release) — start now.
2. **211 NDP outreach** to the 4 local United Ways (parallel emails) — biggest data unlock.
3. **Feeding America HSDS** terms — food at scale.
4. **findhelp** — only if 1–3 leave gaps.

Each is an email + a short call. The tool already works on open data today; these
turn it from "good coverage" into "comprehensive." None require code until a feed
key / terms arrive — then it's one connector each (already stubbed in `sources.yaml`).
