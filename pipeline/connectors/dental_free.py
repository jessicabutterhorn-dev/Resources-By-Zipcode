#!/usr/bin/env python3
"""Connector: FREE non-profit dental resources (KS + MO).

Loads the strictly-verified records from the `free-dental` workflow
(data/dental_records.json). The workflow only keeps resources confirmed FREE +
non-profit (sliding-scale / for-profit / dental-school / Medicaid-only rejected).

Two kinds:
  * 'site'    — a free charitable clinic with a walk-in address -> geocoded,
                service_area = its county.
  * 'program' — by-application (Dental Lifeline / Donated Dental Services) or an
                annual free event (Mission of Mercy) with no fixed address ->
                shown across all counties of the zone it serves.

bucket = 'dental'. Honest by design: if the workflow found none for a zone,
nothing loads there. Requires load_geography.py first. Stdlib only.
"""
import json, os, re, sqlite3, sys, time, hashlib, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "db", "resources.db")
RECORDS = os.path.join(ROOT, "data", "dental_records.json")
UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
CENSUS_ONELINE = ("https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
                  "?benchmark=Public_AR_Current&vintage=Current_Current&format=json&layers=Counties")
CENSUS_DELAY = 0.5
SOURCE_ID = "free-dental"
DIR_URL = "https://dentallifeline.org/"
TODAY = "2026-06-24"

def sid(*p): return hashlib.sha1("|".join(str(x) for x in p).encode()).hexdigest()[:24]

def geocode(addr):
    try:
        req = urllib.request.Request(f"{CENSUS_ONELINE}&address={urllib.parse.quote(addr)}",
                                     headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode("utf-8"))
        ms = d["result"]["addressMatches"]
        if not ms: return None
        g = ms[0]["geographies"]["Counties"][0]
        return {"fips": g["GEOID"], "lat": ms[0]["coordinates"]["y"], "lon": ms[0]["coordinates"]["x"]}
    except Exception as e:
        sys.stderr.write(f"  geocode fail [{addr}]: {e}\n"); return None

def load(dry_run=False):
    if not os.path.exists(RECORDS):
        sys.exit(f"missing {RECORDS} — run the free-dental workflow first")
    recs = json.load(open(RECORDS))
    recs = recs.get("records", recs) if isinstance(recs, dict) else recs
    con = sqlite3.connect(DB); con.execute("PRAGMA foreign_keys=ON"); cur = con.cursor()
    zone_counties = {}
    for fips, zid in cur.execute("SELECT fips, zone_id FROM county_zone"):
        zone_counties.setdefault(zid, []).append(fips)
    known = {r[0] for r in cur.execute("SELECT fips FROM county")}

    if not dry_run:
        cur.execute("""INSERT OR REPLACE INTO source
            (id,source_name,source_type,publisher,source_url,robots_checked,license,attribution_text,
             attribution_required,redistribution_ok,access_route,refresh_mode,date_checked,confidence,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (SOURCE_ID, "Free non-profit dental resources (KS+MO)", "other", "various nonprofits",
             DIR_URL, 1, "org-public-facts", "Free/charitable dental resources — verify with each org", 0, 1,
             "open", "snapshot", TODAY, "medium",
             "Extracted + strictly verified (free + non-profit only) via free-dental workflow."))

    stats = {"in": len(recs), "sites": 0, "programs": 0, "no_geo": 0, "areas": 0, "skipped": 0}
    for r in recs:
        name = (r.get("name") or "").strip()
        kind = r.get("kind")
        if not name: stats["skipped"] += 1; continue
        conf = r.get("confidence") or "medium"
        what = r.get("what")
        phone, web, src = r.get("phone"), r.get("website"), (r.get("source_url") or DIR_URL)

        # target counties + optional office location
        office_fips = lat = lon = addr1 = city = zipc = state = None
        served = set()
        if kind == "site" and r.get("address") and r.get("city"):
            st = r.get("state")
            g = geocode(f"{r['address']}, {r['city']}, {st or ''} {r.get('zip') or ''}".strip())
            time.sleep(CENSUS_DELAY)
            if g and g["fips"] in known:
                office_fips, lat, lon = g["fips"], g["lat"], g["lon"]
                addr1, city, zipc = r["address"], r["city"], (r.get("zip") if r.get("zip") and re.fullmatch(r"\d{5}", r["zip"]) else None)
                state = {"29": "MO", "20": "KS"}[office_fips[:2]]
                served = {office_fips}
        if not served:
            # program (or un-geocodable site) -> cover the whole zone it serves
            served = set(zone_counties.get(r.get("zone_id"), []))
            kind = "program" if kind != "site" else kind
        if not served:
            stats["no_geo"] += 1; continue

        # sites keyed by name+zip; programs keyed by name only -> the same
        # statewide program found in several zones collapses to one org whose
        # service_area accumulates (unions) every zone's counties.
        org_id = sid("dental", name, zipc) if office_fips else sid("dental", name)
        loc_id = sid("loc", org_id); svc_id = sid("svc", org_id)
        if dry_run:
            print(f"  OK [{kind:7}] {name[:38]:38} {('site '+str(office_fips)) if office_fips else ('zone '+str(r.get('zone_id'))+' ('+str(len(served))+' co)')}")
            stats["sites" if kind == "site" else "programs"] += 1
            continue

        cur.execute("INSERT OR REPLACE INTO organization (id,name,website,source_id,source_url,date_checked,confidence) VALUES (?,?,?,?,?,?,?)",
                    (org_id, name, web, SOURCE_ID, src, TODAY, conf))
        cur.execute("""INSERT OR REPLACE INTO location (id,organization_id,name,location_type,latitude,longitude,source_id,source_url,date_checked,confidence)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (loc_id, org_id, name, "physical" if office_fips else "virtual", lat, lon, SOURCE_ID, src, TODAY, conf))
        cur.execute("""INSERT OR REPLACE INTO address (id,location_id,address_1,city,state_province,postal_code,fips,zone_id)
                       VALUES (?,?,?,?,?,?,?, (SELECT zone_id FROM county_zone WHERE fips=?))""",
                    (sid("addr", loc_id), loc_id, addr1, city, state, zipc, office_fips, office_fips))
        if zipc and office_fips:
            cur.execute("INSERT OR IGNORE INTO zip_county (zip,fips,is_primary,crosswalk_vintage,source_id) VALUES (?,?,1,?,?)",
                        (zipc, office_fips, "census-derived", SOURCE_ID))
        cur.execute("""INSERT OR REPLACE INTO service (id,organization_id,name,description,resource_bucket,status,source_id,source_url,date_checked,confidence)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (svc_id, org_id, "Free dental care", what, "dental", "active", SOURCE_ID, src, TODAY, conf))
        cur.execute("INSERT OR IGNORE INTO service_at_location (id,service_id,location_id) VALUES (?,?,?)",
                    (sid("sal", svc_id, loc_id), svc_id, loc_id))
        for f in served:
            cur.execute("INSERT OR IGNORE INTO service_area (id,service_id,extent_type,fips,description) VALUES (?,?,?,?,?)",
                        (sid("sa", svc_id, f), svc_id, "county", f, kind))
            stats["areas"] += 1
        if phone:
            cur.execute("INSERT OR REPLACE INTO phone (id,organization_id,number,type) VALUES (?,?,?,?)",
                        (sid("ph", org_id), org_id, phone, "voice"))
        cur.execute("""INSERT OR REPLACE INTO record_provenance (id,record_table,record_id,source_id,source_url,date_checked,confidence,extracted_by,method)
                       VALUES (?,?,?,?,?,?,?,?,?)""",
                    (sid("prov", org_id), "organization", org_id, SOURCE_ID, src, TODAY, conf, "automated", "workflow_extraction"))
        stats["sites" if office_fips else "programs"] += 1

    if not dry_run:
        cur.execute("""INSERT INTO refresh_log (id,run_started,run_finished,refresh_quarter,source_id,stage,status,records_in,records_out,records_rejected,message)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (sid("run", SOURCE_ID, TODAY), TODAY, TODAY, "2026Q2", SOURCE_ID, "load", "success",
                     stats["in"], stats["sites"] + stats["programs"], stats["skipped"],
                     f"sites={stats['sites']} programs={stats['programs']} areas={stats['areas']}"))
        con.commit()
    con.close()
    print(f"[free-dental] sites={stats['sites']} programs={stats['programs']} "
          f"service_areas={stats['areas']} no_geo={stats['no_geo']} skipped={stats['skipped']}")
    return stats

if __name__ == "__main__":
    load(dry_run="--dry-run" in sys.argv)
