#!/usr/bin/env python3
"""Curated source: St. Louis hygiene / personal-care-kit providers.

Hygiene / personal-care kits are a need category not covered by the open food
and utility feeds. This is a MANUALLY CURATED list (St. Louis metro) provided
to the project, loaded as a starting set.

PROVENANCE / TRUST:
  * These rows are loaded with confidence='unverified' and source_type
    'manual_verify'. The front-end flags unverified records with a badge.
  * Only entries with a clear name + street address are included here (so they
    geocode and appear in ZIP search). Nothing is invented; phone/area-only
    leads were intentionally left out pending confirmation.
  * Each org's own website is the source_url where known; otherwise the
    Start Here STL directory is the pointer. VERIFY against the org before
    relying — hours/handout days change often for street outreach.

Path: in-file curated list -> geocode (Census one-line -> county FIPS) ->
verify (county in KS/MO spine) -> load bucket='hygiene'. Run load_geography
first. Stdlib only.
"""
import os, re, sqlite3, sys, time, hashlib, urllib.parse, urllib.request, json

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "db", "resources.db")
UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
CENSUS_ONELINE = ("https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
                  "?benchmark=Public_AR_Current&vintage=Current_Current&format=json&layers=Counties")
CENSUS_DELAY = 0.5
SOURCE_ID = "hygiene-stl-curated"
DIRECTORY_URL = "https://www.startherestl.org/"
TODAY = "2026-06-24"
CONFIDENCE = "unverified"      # curated, not source-confirmed -> page shows the badge

# Only entries with an unambiguous name + street address (geocodable).
# Fields: name, street, city, state, zip(optional), phone(optional),
#         website(optional), what(short factual note).
CURATED = [
    {"name": "New Life Evangelistic Center", "street": "2428 Woodson Rd", "city": "Overland",
     "state": "MO", "zip": "63114", "phone": "(314) 421-3020",
     "website": "newlifeevangelisticcenter.org/get-help/care-kits",
     "what": "Daily 'Care Kits' street handout: shampoo, toothbrush/paste, deodorant, soap, washcloth, razor, lotion; women's add feminine products."},
    {"name": "inExcelsis (Dignity on Wheels)", "street": "4265 Shaw Blvd", "city": "St. Louis",
     "state": "MO", "zip": "63110", "phone": "(314) 887-7156", "website": "inexcelsislove.org",
     "what": "Hygiene kits, wipes, underwear, bus tickets, mobile showers (Apr-Nov). Walk-in Sat 8-11am."},
    {"name": "St. Patrick Center", "street": "800 N Tucker Blvd", "city": "St. Louis",
     "state": "MO", "zip": None, "phone": "(314) 802-0700", "website": None,
     "what": "Hygiene kits, men's/women's/period kits, mobile showers daily."},
    {"name": "Bridge of Hope (the Ville)", "street": "4001 Cottage Ave", "city": "St. Louis",
     "state": "MO", "zip": None, "phone": "(314) 405-0253", "website": None,
     "what": "Toiletries room, showers, laundry; drop-in Mon/Wed/Thu/Sat 9am."},
    {"name": "Isaiah 58 Ministries", "street": "2149 S Grand Blvd", "city": "St. Louis",
     "state": "MO", "zip": None, "phone": "(314) 776-1410", "website": None,
     "what": "Shower ministry, hygiene items, undergarments; Wed 9am-12."},
    {"name": "Covenant House Missouri (youth 16-24)", "street": "2727 N Kingshighway", "city": "St. Louis",
     "state": "MO", "zip": None, "phone": "(314) 533-2241", "website": None,
     "what": "'Cov Closet' free hygiene + clothing, 24/7 (youth 16-24)."},
    {"name": "Loaves & Fishes", "street": "2750 McKelvey Rd", "city": "Maryland Heights",
     "state": "MO", "zip": None, "phone": None, "website": None,
     "what": "Hygiene items for shelter + veteran clients."},
    {"name": "St. Anthony's Food Pantry", "street": "3140 S Meramec St", "city": "St. Louis",
     "state": "MO", "zip": None, "phone": None, "website": None,
     "what": "Food pantry that also gives personal-care items; no ID needed."},
    {"name": "Carondelet UCC Free Store", "street": "7423 Michigan Ave", "city": "St. Louis",
     "state": "MO", "zip": None, "phone": "(314) 353-0607", "website": None,
     "what": "Hygiene/household free store; 2nd Sat monthly."},
    {"name": "Transformation Christian Free Store", "street": "4071 Page Blvd", "city": "St. Louis",
     "state": "MO", "zip": None, "phone": "(314) 535-1176", "website": None,
     "what": "Free store: toiletries and household items."},
]

def sid(*p):
    return hashlib.sha1("|".join(str(x) for x in p).encode()).hexdigest()[:24]

def geocode(rec):
    addr = f"{rec['street']}, {rec['city']}, {rec['state']}" + (f" {rec['zip']}" if rec.get("zip") else "")
    try:
        req = urllib.request.Request(f"{CENSUS_ONELINE}&address={urllib.parse.quote(addr)}",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8"))
        ms = d["result"]["addressMatches"]
        if not ms:
            return None
        g = ms[0]["geographies"]["Counties"][0]
        return {"fips": g["GEOID"], "lat": ms[0]["coordinates"]["y"], "lon": ms[0]["coordinates"]["x"]}
    except Exception as e:
        sys.stderr.write(f"  geocode fail [{addr}]: {e}\n")
        return None

def load(dry_run=False):
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()
    known_fips = {r[0] for r in cur.execute("SELECT fips FROM county")}
    if not dry_run:
        cur.execute("""INSERT OR REPLACE INTO source
            (id, source_name, source_type, publisher, source_url, robots_checked,
             license, attribution_text, attribution_required, redistribution_ok,
             access_route, refresh_mode, date_checked, confidence, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (SOURCE_ID, "Curated St. Louis hygiene / personal-care providers", "manual_verify",
             "project-curated", DIRECTORY_URL, 0, "curated-facts",
             "St. Louis area hygiene resources (curated; verify with each org)", 0, 1,
             "open", "snapshot", TODAY, CONFIDENCE,
             "Manually curated leads. UNVERIFIED until confirmed against each org. Street-outreach hours change often."))

    stats = {"in": len(CURATED), "loaded": 0, "no_geo": 0}
    for rec in CURATED:
        geo = geocode(rec)
        time.sleep(CENSUS_DELAY)
        if not geo or geo["fips"] not in known_fips:
            stats["no_geo"] += 1
            sys.stderr.write(f"  SKIP (no county): {rec['name']}\n")
            continue
        fips = geo["fips"]
        src_url = ("https://" + rec["website"]) if rec.get("website") else DIRECTORY_URL
        if dry_run:
            print(f"  OK {rec['name'][:36]:36} {rec['city']},{rec['state']} -> {fips}")
            stats["loaded"] += 1
            continue
        org_id = sid("hyg", rec["name"]); loc_id = sid("loc", org_id); svc_id = sid("svc", org_id)
        cur.execute("""INSERT OR REPLACE INTO organization (id,name,website,source_id,source_url,date_checked,confidence)
                       VALUES (?,?,?,?,?,?,?)""",
                    (org_id, rec["name"], rec.get("website"), SOURCE_ID, src_url, TODAY, CONFIDENCE))
        cur.execute("""INSERT OR REPLACE INTO location
            (id,organization_id,name,location_type,latitude,longitude,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (loc_id, org_id, rec["name"], "physical", geo["lat"], geo["lon"], SOURCE_ID, src_url, TODAY, CONFIDENCE))
        cur.execute("""INSERT OR REPLACE INTO address
            (id,location_id,address_1,city,state_province,postal_code,fips,zone_id)
            VALUES (?,?,?,?,?,?,?, (SELECT zone_id FROM county_zone WHERE fips=?))""",
            (sid("addr", loc_id), loc_id, rec["street"], rec["city"], rec["state"], rec.get("zip"), fips, fips))
        if rec.get("zip"):
            pass  # zip_county via load_zip_county.py (Census crosswalk)
        cur.execute("""INSERT OR REPLACE INTO service
            (id,organization_id,name,description,resource_bucket,status,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (svc_id, org_id, "Hygiene / personal-care kits", rec.get("what"), "hygiene", "active",
             SOURCE_ID, src_url, TODAY, CONFIDENCE))
        cur.execute("INSERT OR IGNORE INTO service_at_location (id,service_id,location_id) VALUES (?,?,?)",
                    (sid("sal", svc_id, loc_id), svc_id, loc_id))
        cur.execute("""INSERT OR IGNORE INTO service_area (id,service_id,extent_type,fips,description)
                       VALUES (?,?,?,?,?)""", (sid("sa", svc_id, fips), svc_id, "county", fips, "Site county"))
        if rec.get("phone"):
            cur.execute("INSERT OR REPLACE INTO phone (id,organization_id,number,type) VALUES (?,?,?,?)",
                        (sid("ph", org_id), org_id, rec["phone"], "voice"))
        cur.execute("""INSERT OR REPLACE INTO record_provenance
            (id,record_table,record_id,source_id,source_url,date_checked,confidence,extracted_by,method)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (sid("prov", org_id), "organization", org_id, SOURCE_ID, src_url, TODAY,
             CONFIDENCE, "human", "manual_curation"))
        stats["loaded"] += 1

    if not dry_run:
        cur.execute("""INSERT INTO refresh_log
            (id,run_started,run_finished,refresh_quarter,source_id,stage,status,records_in,records_out,records_rejected,message)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (sid("run", SOURCE_ID, TODAY), TODAY, TODAY, "2026Q2", SOURCE_ID, "load", "success",
             stats["in"], stats["loaded"], 0, f"no_geo={stats['no_geo']} (unverified curated)"))
        con.commit()
    con.close()
    return stats

def main():
    dry = "--dry-run" in sys.argv
    print(f"[hygiene-stl] {len(CURATED)} curated entries. {'DRY RUN' if dry else 'loading (unverified)'} ...")
    s = load(dry_run=dry)
    print(f"[hygiene-stl] loaded={s['loaded']} no_geo={s['no_geo']} (all confidence=unverified)")

if __name__ == "__main__":
    main()
