#!/usr/bin/env python3
"""Connector: KS + MO Area Agencies on Aging (senior services).

Loads the verified AAA records produced by the `ks-mo-aaa-enrich` workflow
(saved to data/aaa_records.json). Each AAA serves a multi-county region
(modeled as HSDS service_area) and provides senior services mapped to buckets:
  meals -> food, transportation -> gas_transport, info&referral -> navigation.

This is how the workflow output reaches the DB: workflow agents do the
robots-checked safe-route extraction + adversarial verification; this connector
geocodes the office, resolves served counties to FIPS, and loads.

Requires load_geography.py first. Stdlib only.

Usage: python3 pipeline/connectors/aaa_seniors.py [--dry-run]
"""
import json, os, re, sqlite3, sys, time, hashlib, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "db", "resources.db")
RECORDS = os.path.join(ROOT, "data", "aaa_records.json")
UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
CENSUS_ONELINE = ("https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
                  "?benchmark=Public_AR_Current&vintage=Current_Current&format=json&layers=Counties")
CENSUS_DELAY = 0.5
SOURCE_ID = "ks-mo-aaa"
DIR_URL = "https://eldercare.acl.gov/"
TODAY = "2026-06-24"
SVC_NAME = {"food": "Senior meals (home-delivered & congregate)",
            "gas_transport": "Senior transportation",
            "navigation": "Aging info & referral / options counseling"}

def sid(*p): return hashlib.sha1("|".join(str(x) for x in p).encode()).hexdigest()[:24]
def norm(n): return re.sub(r"[^a-z ]", "", (n or "").lower()).replace(" county", "").strip()

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
        sys.exit(f"missing {RECORDS} — run the ks-mo-aaa-enrich workflow first")
    recs = json.load(open(RECORDS))
    recs = recs.get("records", recs) if isinstance(recs, dict) else recs
    con = sqlite3.connect(DB); con.execute("PRAGMA foreign_keys=ON"); cur = con.cursor()
    name2fips = {}
    for fips, cname, st in cur.execute("SELECT fips,county_name,state FROM county"):
        name2fips[(st, norm(cname))] = fips

    if not dry_run:
        cur.execute("""INSERT OR REPLACE INTO source
            (id,source_name,source_type,publisher,source_url,robots_checked,license,attribution_text,
             attribution_required,redistribution_ok,access_route,refresh_mode,date_checked,confidence,notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (SOURCE_ID, "KS & MO Area Agencies on Aging", "gov_web_page",
             "Area Agencies on Aging (KDADS / MO DHSS / ACL network)", DIR_URL, 1,
             "gov-public-facts", "Source: Kansas & Missouri Area Agencies on Aging", 1, 1,
             "open", "snapshot", TODAY, "medium",
             "Extracted + adversarially verified via ks-mo-aaa-enrich workflow. Senior meals/transport/referral."))

    st_stats = {"KS": 0, "MO": 0}
    stats = {"in": len(recs), "loaded": 0, "no_geo": 0, "skipped": 0, "areas": 0}
    for r in recs:
        name = (r.get("name") or "").strip()
        state = r.get("state")
        if not name or state not in ("KS", "MO"):
            stats["skipped"] += 1; continue
        conf = "low" if r.get("plausible") is False else (r.get("confidence") or "medium")

        # served counties -> fips
        served = set()
        for cn in (r.get("counties_served") or []):
            f = name2fips.get((state, norm(cn)))
            if f: served.add(f)

        # office geocode (for display address + a fallback county)
        office_fips = None; lat = lon = None
        if r.get("address") and r.get("city"):
            g = geocode(f"{r['address']}, {r['city']}, {state}" + (f" {r['zip']}" if r.get('zip') else ""))
            time.sleep(CENSUS_DELAY)
            if g: office_fips, lat, lon = g["fips"], g["lat"], g["lon"]
        if office_fips: served.add(office_fips)
        if not served:
            stats["no_geo"] += 1; continue

        services = r.get("services") or ["navigation"]
        if dry_run:
            print(f"  OK [{conf:6}] {name[:38]:38} {state}  {len(served)} counties  svc={','.join(services)}")
            stats["loaded"] += 1; st_stats[state] += 1; continue

        org_id = sid("aaa", name, state); loc_id = sid("loc", org_id)
        src_url = r.get("source_url") or DIR_URL
        cur.execute("""INSERT OR REPLACE INTO organization (id,name,email,website,source_id,source_url,date_checked,confidence)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (org_id, name, r.get("email"), r.get("website"), SOURCE_ID, src_url, TODAY, conf))
        cur.execute("""INSERT OR REPLACE INTO location
            (id,organization_id,name,location_type,latitude,longitude,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (loc_id, org_id, name, "physical", lat, lon, SOURCE_ID, src_url, TODAY, conf))
        cur.execute("""INSERT OR REPLACE INTO address
            (id,location_id,address_1,city,state_province,postal_code,fips,zone_id)
            VALUES (?,?,?,?,?,?,?, (SELECT zone_id FROM county_zone WHERE fips=?))""",
            (sid("addr", loc_id), loc_id, r.get("address"), r.get("city"), state, r.get("zip"),
             office_fips, office_fips))
        if r.get("zip") and office_fips and re.fullmatch(r"\d{5}", r["zip"]):
            pass  # zip_county via load_zip_county.py (Census crosswalk)
        if r.get("phone"):
            cur.execute("INSERT OR REPLACE INTO phone (id,organization_id,number,type) VALUES (?,?,?,?)",
                        (sid("ph", org_id), org_id, r["phone"], "voice"))
        cur.execute("""INSERT OR REPLACE INTO record_provenance
            (id,record_table,record_id,source_id,source_url,date_checked,confidence,extracted_by,method)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (sid("prov", org_id), "organization", org_id, SOURCE_ID, src_url, TODAY, conf, "automated", "workflow_extraction"))

        for b in services:
            if b not in SVC_NAME: continue
            svc_id = sid("svc", org_id, b)
            cur.execute("""INSERT OR REPLACE INTO service (id,organization_id,name,resource_bucket,status,source_id,source_url,date_checked,confidence)
                           VALUES (?,?,?,?,?,?,?,?,?)""",
                        (svc_id, org_id, SVC_NAME[b], b, "active", SOURCE_ID, src_url, TODAY, conf))
            cur.execute("INSERT OR IGNORE INTO service_at_location (id,service_id,location_id) VALUES (?,?,?)",
                        (sid("sal", svc_id, loc_id), svc_id, loc_id))
            for f in served:
                cur.execute("INSERT OR IGNORE INTO service_area (id,service_id,extent_type,fips,description) VALUES (?,?,?,?,?)",
                            (sid("sa", svc_id, f), svc_id, "county", f, "AAA planning service area"))
                stats["areas"] += 1
        stats["loaded"] += 1; st_stats[state] += 1

    if not dry_run:
        cur.execute("""INSERT INTO refresh_log (id,run_started,run_finished,refresh_quarter,source_id,stage,status,records_in,records_out,records_rejected,message)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (sid("run", SOURCE_ID, TODAY), TODAY, TODAY, "2026Q2", SOURCE_ID, "load", "success",
                     stats["in"], stats["loaded"], stats["skipped"],
                     f"KS={st_stats['KS']} MO={st_stats['MO']} service_areas={stats['areas']} no_geo={stats['no_geo']}"))
        con.commit()
    con.close()
    print(f"[ks-mo-aaa] loaded={stats['loaded']} (KS={st_stats['KS']} MO={st_stats['MO']}) "
          f"service_areas={stats['areas']} no_geo={stats['no_geo']} skipped={stats['skipped']}")
    return stats

if __name__ == "__main__":
    load(dry_run="--dry-run" in sys.argv)
