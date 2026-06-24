# KS + MO SSBCI Community Resource Directory

Private repo. **Public-source data only. NO PHI / PII, ever.**

**Purpose:** safety net for Kansas + Missouri Medicare members who lose SSBCI /
flex / grocery-card benefits when CMS-4208-F (CY2027 MA Final Rule) takes effect
**1/1/2027**. Members enter a ZIP and see (a) what they may be losing and (b)
verified local food / utility / rent / pet-food / gas / prescription help.

Status: **SCAFFOLD + DEMO** (sample data only — no real collection yet).

## Try the demo

```bash
./build.sh                     # rebuild DB + front-end data from schema + seed
open frontend/index.html       # or just double-click it
```

Demo ZIPs: **64111** (Kansas City MO), **66061** (Olathe KS), **65806** (Springfield MO).
All listings are fictional `[SAMPLE]` placeholders — the page shows a SAMPLE banner.

## Layout

```
db/schema.sql        SQLite schema (HSDS core + geo/zone spine + carrier layer + provenance)
db/seed.sql          FICTIONAL demo rows (delete before production load)
db/resources.db      built DB (gitignored)
pipeline/            quarterly refresh pipeline + build_frontend.py (DB -> static data.js)
frontend/            self-contained printable page (index.html + generated data.js)
data/zones.json      canonical 6-zone -> county map (220 counties)
docs/                research briefs (00 overview, 01 legal, 02 carriers, 03 SSBCI-2027, 04 sources, 05 zones)
agents/              zone-parameterized collector prompt (for future safe-route collection)
```

## Hard constraints (do not deviate)

- **Safe-route sourcing only**: .gov / open data first, OpenReferral HSDS / 211 feeds next,
  findhelp/aggregators for single-fact corroboration only — never bulk scrape. robots.txt + ToS
  checked before any fetch.
- **Verify everything**: every record carries source_url + date_checked + confidence.
- **Zero PHI/PII**: the schema offers no field able to hold member data → HIPAA out of scope by
  construction. A CI tripwire rejects member-shaped fields.
- **Provenance + attribution** tracked per source.

## Before any real data collection — open questions (see `docs/00-overview.md`)

1. IP / governance sign-off (employer ownership; enterprise vs personal GitHub).
2. 211 / United Way data-sharing agreements (statewide HSDS spine is agreement-gated).
3. findhelp relationship (MO DSS already partners — licensed route vs manual corroboration).
4. Carrier scope (all KS+MO MA plans vs Aetna-focused).
