#!/usr/bin/env python3
"""Load the COMPLETE KS+MO ZIP->county crosswalk so every ZIP is searchable.

Without this, a ZIP is only found if an ingested record sits there; ZIPs with no
local office (but covered by regional/statewide resources) returned nothing
(e.g. Emporia KS, Cape Girardeau MO). This loads every KS+MO ZIP -> its
county(ies) from the Census ZCTA<->County relationship file (public domain), so
typing any KS/MO ZIP resolves to its county and shows the regional/statewide/
AAA/211 resources that cover it.

Run after load_geography (needs county fips), before the connectors. Stdlib only.
"""
import os, sqlite3, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "resources.db")
UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
REL = "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/tab20_zcta520_county20_natl.txt"
SOURCE_ID = "census-zcta"

def main():
    con = sqlite3.connect(DB); con.execute("PRAGMA foreign_keys=ON"); cur = con.cursor()
    known = {r[0] for r in cur.execute("SELECT fips FROM county")}
    cur.execute("""INSERT OR REPLACE INTO source
        (id,source_name,source_type,publisher,source_url,robots_checked,license,attribution_text,
         attribution_required,redistribution_ok,access_route,refresh_mode,date_checked,confidence,notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (SOURCE_ID, "Census ZCTA-County relationship (2020)", "gov_open_data", "U.S. Census Bureau",
         REL, 1, "US-Gov-PublicDomain", "Source: U.S. Census Bureau", 0, 1, "open", "snapshot",
         "2026-06-25", "high", "ZIP->county crosswalk so every KS/MO ZIP resolves."))

    req = urllib.request.Request(REL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        text = r.read().decode("utf-8", "replace")

    # rows per zip; pick the county with the largest land-overlap as is_primary
    by_zip = {}
    for line in text.splitlines()[1:]:
        c = line.split("|")
        if len(c) < 17:
            continue
        zipc, cfips = c[1].strip(), c[9].strip()
        if cfips not in known:
            continue
        try:
            land = float(c[16] or 0)
        except ValueError:
            land = 0.0
        by_zip.setdefault(zipc, []).append((cfips, land))

    added = 0
    for zipc, pairs in by_zip.items():
        primary = max(pairs, key=lambda p: p[1])[0]
        for cfips, _land in pairs:
            cur.execute("""INSERT OR IGNORE INTO zip_county
                (zip,fips,is_primary,crosswalk_vintage,source_id) VALUES (?,?,?,?,?)""",
                (zipc, cfips, 1 if cfips == primary else 0, "2020-census", SOURCE_ID))
            added += cur.rowcount
    con.commit()
    n_zip = cur.execute("SELECT count(DISTINCT zip) FROM zip_county").fetchone()[0]
    con.close()
    print(f"[zip-county] {len(by_zip)} KS+MO ZIPs in crosswalk; {added} new rows; {n_zip} total ZIPs searchable")

if __name__ == "__main__":
    main()
