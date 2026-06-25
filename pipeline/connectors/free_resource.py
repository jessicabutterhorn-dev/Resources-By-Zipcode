#!/usr/bin/env python3
"""Generic loader for workflow-verified free/charitable resources.

Parameterized by bucket — used for prescription, rent, pet_food (and reusable
for any future free-resource bucket). Reads a records JSON produced by a
per-zone "find + adversarially verify" workflow and loads:
  * 'site'    — a fixed walk-in location -> geocoded, service_area = its county.
  * 'program' — by-application / area-wide -> shown across the zone it serves
                (no fixed address; the regional display rule hides far HQ).

Mirrors dental_free.py / vision_free.py but bucket/source are CLI args.
Requires load_geography.py first. Stdlib only.

Usage:
  python3 pipeline/connectors/free_resource.py \\
    --bucket prescription --records data/rx_records.json \\
    --source-id rx-assist --source-name "Free/charitable prescription assistance (KS+MO)" \\
    --service-name "Prescription assistance" --dir-url https://www.needymeds.org/ [--dry-run]
"""
import argparse, json, os, re, sqlite3, sys, time, hashlib, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "db", "resources.db")
UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
CENSUS_ONELINE = ("https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
                  "?benchmark=Public_AR_Current&vintage=Current_Current&format=json&layers=Counties")
CENSUS_DELAY = 0.5
TODAY = "2026-06-25"

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

def load(bucket, records_path, source_id, source_name, service_name, dir_url, dry_run=False):
    if not os.path.exists(records_path):
        sys.exit(f"missing {records_path} — run the workflow first")
    recs = json.load(open(records_path))
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
            (source_id, source_name, "other", "various nonprofits", dir_url, 1, "org-public-facts",
             f"{service_name} — verify with each org", 0, 1, "open", "snapshot", TODAY, "medium",
             f"Extracted + strictly verified (free/charitable only) via the {source_id} workflow."))

    stats = {"in": len(recs), "sites": 0, "programs": 0, "no_geo": 0, "areas": 0, "skipped": 0}
    for r in recs:
        name = (r.get("name") or "").strip()
        kind = r.get("kind")
        if not name: stats["skipped"] += 1; continue
        conf = r.get("confidence") or "medium"
        what, phone = r.get("what"), r.get("phone")
        web, src = r.get("website"), (r.get("source_url") or dir_url)

        office_fips = lat = lon = addr1 = city = zipc = state = None
        served = set()
        if kind == "site" and r.get("address") and r.get("city"):
            st = r.get("state")
            g = geocode(f"{r['address']}, {r['city']}, {st or ''} {r.get('zip') or ''}".strip())
            time.sleep(CENSUS_DELAY)
            if g and g["fips"] in known:
                office_fips, lat, lon = g["fips"], g["lat"], g["lon"]
                addr1, city = r["address"], r["city"]
                zipc = r.get("zip") if r.get("zip") and re.fullmatch(r"\d{5}", r["zip"] or "") else None
                state = {"29": "MO", "20": "KS"}[office_fips[:2]]
                served = {office_fips}
        if not served:
            served = set(zone_counties.get(r.get("zone_id"), []))
            kind = "program" if kind != "site" else kind
        if not served:
            stats["no_geo"] += 1; continue

        org_id = sid(source_id, name, zipc) if office_fips else sid(source_id, name)
        loc_id = sid("loc", org_id); svc_id = sid("svc", org_id)
        if dry_run:
            print(f"  OK [{kind:7}] {name[:38]:38} {('site '+str(office_fips)) if office_fips else ('zone '+str(r.get('zone_id'))+' ('+str(len(served))+'co)')}")
            stats["sites" if office_fips else "programs"] += 1
            continue

        cur.execute("INSERT OR REPLACE INTO organization (id,name,website,source_id,source_url,date_checked,confidence) VALUES (?,?,?,?,?,?,?)",
                    (org_id, name, web, source_id, src, TODAY, conf))
        cur.execute("""INSERT OR REPLACE INTO location (id,organization_id,name,location_type,latitude,longitude,source_id,source_url,date_checked,confidence)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (loc_id, org_id, name, "physical" if office_fips else "virtual", lat, lon, source_id, src, TODAY, conf))
        cur.execute("""INSERT OR REPLACE INTO address (id,location_id,address_1,city,state_province,postal_code,fips,zone_id)
                       VALUES (?,?,?,?,?,?,?, (SELECT zone_id FROM county_zone WHERE fips=?))""",
                    (sid("addr", loc_id), loc_id, addr1, city, state, zipc, office_fips, office_fips))
        if zipc and office_fips:
            cur.execute("INSERT OR IGNORE INTO zip_county (zip,fips,is_primary,crosswalk_vintage,source_id) VALUES (?,?,1,?,?)",
                        (zipc, office_fips, "census-derived", source_id))
        cur.execute("""INSERT OR REPLACE INTO service (id,organization_id,name,description,resource_bucket,status,source_id,source_url,date_checked,confidence)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (svc_id, org_id, service_name, what, bucket, "active", source_id, src, TODAY, conf))
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
                    (sid("prov", org_id), "organization", org_id, source_id, src, TODAY, conf, "automated", "workflow_extraction"))
        stats["sites" if office_fips else "programs"] += 1

    if not dry_run:
        cur.execute("""INSERT INTO refresh_log (id,run_started,run_finished,refresh_quarter,source_id,stage,status,records_in,records_out,records_rejected,message)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (sid("run", source_id, TODAY), TODAY, TODAY, "2026Q2", source_id, "load", "success",
                     stats["in"], stats["sites"] + stats["programs"], stats["skipped"],
                     f"bucket={bucket} sites={stats['sites']} programs={stats['programs']} areas={stats['areas']}"))
        con.commit()
    con.close()
    print(f"[{source_id}] bucket={bucket} sites={stats['sites']} programs={stats['programs']} "
          f"service_areas={stats['areas']} no_geo={stats['no_geo']} skipped={stats['skipped']}")
    return stats

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", required=True)
    ap.add_argument("--records", required=True)
    ap.add_argument("--source-id", required=True)
    ap.add_argument("--source-name", required=True)
    ap.add_argument("--service-name", required=True)
    ap.add_argument("--dir-url", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    load(a.bucket, a.records, a.source_id, a.source_name, a.service_name, a.dir_url, a.dry_run)

if __name__ == "__main__":
    main()
