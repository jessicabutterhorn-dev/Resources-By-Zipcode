#!/usr/bin/env python3
"""Connector: Operation Food Search food locations (St. Louis metro, zone 2).

Operation Food Search (operationfoodsearch.org) is a major St. Louis-area
hunger-relief org. Their /find-food/ map uses the WP Store Locator plugin,
whose admin-ajax `store_search` action returns CLEAN JSON (name, address,
city, state, zip, lat/lng, phone, email, hours) — a structured feed, not a
scrape. This is the densest food source for eastern Missouri.

REUSABLE PATTERN: any WordPress site with `wpsl` / store-locator + admin-ajax
exposes this same store_search JSON. Probe new food orgs for it first.

SAFE-ROUTE: robots.txt explicitly Allows /wp-admin/admin-ajax.php (Crawl-delay
10; one query here). Facts only; attribution to Operation Food Search;
provenance + confidence per record; PII tripwire. Illinois rows auto-excluded
(their county FIPS aren't in the KS/MO spine).

Path: ingest (store_search JSON) -> normalize (HSDS) -> geocode (Census coords
in-data -> county FIPS) -> verify -> load. Requires load_geography.py first.

Stdlib only.
"""
import json, os, re, sqlite3, sys, time, hashlib, html, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "db", "resources.db")
RAW_DIR = os.path.join(ROOT, "data", "raw", "ofs_metro")

UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
AJAX = ("https://www.operationfoodsearch.org/wp-admin/admin-ajax.php"
        "?action=store_search&lat=38.627&lng=-90.199&max_results=3000&radius=600")
SITE_URL = "https://www.operationfoodsearch.org/find-food/"
CENSUS_GEO = ("https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
              "?benchmark=Public_AR_Current&vintage=Current_Current&format=json&layers=Counties")
CENSUS_DELAY = 0.4
SOURCE_ID = "ofs-metro"
TODAY = "2026-06-24"
CONFIDENCE = "medium"

PHONE_RE = re.compile(r"^\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}(?:\s*(?:ext|x)\.?\s*\d+)?$", re.I)
PII_KEY_PAT = re.compile(r"\b(ssn|dob|member.?id|medicare.?id|beneficiary|claim|diagnosis)\b", re.I)
PII_VAL_PAT = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

def _get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read().decode("utf-8", "replace")
    return data if raw else json.loads(data)

def sid(*p):
    return hashlib.sha1("|".join(str(x) for x in p).encode()).hexdigest()[:24]

_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
_ABBR = {"Monday": "Mon", "Tuesday": "Tue", "Wednesday": "Wed", "Thursday": "Thu",
         "Friday": "Fri", "Saturday": "Sat", "Sunday": "Sun"}

def clean_hours(h):
    """Turn the per-day hours table into a compact line, grouping consecutive
    days with the same hours: 'Mon-Fri 8:00 AM - 4:00 PM, Sat-Sun closed'."""
    if not h:
        return None
    t = html.unescape(re.sub(r"<[^>]+>", " ", h))
    t = re.sub(r"\s+", " ", t).strip()
    if not t:
        return None
    pairs = re.findall(r"(" + "|".join(_DAYS) + r")\s+(.*?)(?=(?:" + "|".join(_DAYS) + r")|$)", t)
    if not pairs:
        return t   # not the expected per-day format; return cleaned text as-is
    dayhours = {}
    for day, val in pairs:
        v = val.strip(" -").strip()
        dayhours[day] = "closed" if (not v or v.lower().startswith("closed")) else v
    groups = []   # [start_day, end_day, hours]
    for d in _DAYS:
        if d not in dayhours:
            continue
        v = dayhours[d]
        if groups and groups[-1][2] == v:
            groups[-1][1] = d
        else:
            groups.append([d, d, v])
    parts = []
    for start, end, v in groups:
        label = _ABBR[start] if start == end else f"{_ABBR[start]}-{_ABBR[end]}"
        parts.append(f"{label} closed" if v == "closed" else f"{label} {v}")
    return ", ".join(parts) or None

def geocode_county(lat, lon):
    try:
        d = _get(f"{CENSUS_GEO}&x={lon}&y={lat}")
        cs = d["result"]["geographies"]["Counties"]
        return cs[0]["GEOID"] if cs else None
    except Exception as e:
        sys.stderr.write(f"  geocode fail ({lat},{lon}): {e}\n")
        return None

def fetch_rows():
    rows = _get(AJAX)
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(os.path.join(RAW_DIR, f"ofs_{TODAY}.json"), "w") as f:
        json.dump(rows, f, indent=1)
    return rows if isinstance(rows, list) else []

def load(rows, dry_run=False):
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
            (SOURCE_ID, "Operation Food Search — food locations", "other",
             "Operation Food Search", SITE_URL, 1,
             "org-public-locator-facts", "Source: Operation Food Search (operationfoodsearch.org)",
             1, 1, "open", "live_api", TODAY, CONFIDENCE,
             "WP Store Locator store_search JSON. robots Allows admin-ajax. Facts only; coords in-data."))

    stats = {"in": len(rows), "rejected_pii": 0, "no_geo": 0, "out_of_area": 0, "loaded": 0}
    for s in rows:
        name = html.unescape((s.get("store") or "")).strip()
        if not name:
            continue
        if PII_KEY_PAT.search(name):
            stats["rejected_pii"] += 1
            continue
        lat, lon = s.get("lat"), s.get("lng")
        if not lat or not lon:
            stats["no_geo"] += 1
            continue
        try:
            fips = geocode_county(float(lat), float(lon))
        except ValueError:
            fips = None
        time.sleep(CENSUS_DELAY)
        if not fips:
            stats["no_geo"] += 1
            continue
        if fips not in known_fips:        # Illinois / outside KS+MO
            stats["out_of_area"] += 1
            continue
        state = {"29": "MO", "20": "KS"}[fips[:2]]

        addr1 = html.unescape((s.get("address") or "")).strip() or None
        addr2 = html.unescape((s.get("address2") or "")).strip() or None
        if addr2:
            addr1 = f"{addr1} {addr2}".strip() if addr1 else addr2
        city = html.unescape((s.get("city") or "")).strip() or None
        zipc = (s.get("zip") or "").strip()
        zipc = zipc if re.fullmatch(r"\d{5}", zipc) else None
        raw_phone = (s.get("phone") or "").strip()
        phone = raw_phone if PHONE_RE.match(raw_phone) else None     # some rows put hours in phone
        email = (s.get("email") or "").strip() or None
        web = (s.get("url") or "").strip() or None
        hours = clean_hours(s.get("hours"))

        if dry_run:
            print(f"  OK {name[:34]:34} {city},{state} {zipc or '-----'}  {fips}  {phone or ''}")
            stats["loaded"] += 1
            continue

        org_id = sid("ofs", name, zipc or addr1)
        loc_id = sid("loc", org_id); svc_id = sid("svc", org_id)
        cur.execute("""INSERT OR REPLACE INTO organization (id,name,email,website,source_id,source_url,date_checked,confidence)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (org_id, name, email, web, SOURCE_ID, SITE_URL, TODAY, CONFIDENCE))
        cur.execute("""INSERT OR REPLACE INTO location
            (id,organization_id,name,location_type,latitude,longitude,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (loc_id, org_id, name, "physical", float(lat), float(lon), SOURCE_ID, SITE_URL, TODAY, CONFIDENCE))
        cur.execute("""INSERT OR REPLACE INTO address
            (id,location_id,address_1,city,state_province,postal_code,fips,zone_id)
            VALUES (?,?,?,?,?,?,?, (SELECT zone_id FROM county_zone WHERE fips=?))""",
            (sid("addr", loc_id), loc_id, addr1, city, state, zipc, fips, fips))
        if zipc:
            cur.execute("""INSERT OR IGNORE INTO zip_county (zip,fips,is_primary,crosswalk_vintage,source_id)
                           VALUES (?,?,1,?,?)""", (zipc, fips, "census-derived", SOURCE_ID))
        cur.execute("""INSERT OR REPLACE INTO service
            (id,organization_id,name,resource_bucket,status,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (svc_id, org_id, "Food distribution / pantry", "food", "active", SOURCE_ID, SITE_URL, TODAY, CONFIDENCE))
        cur.execute("INSERT OR IGNORE INTO service_at_location (id,service_id,location_id) VALUES (?,?,?)",
                    (sid("sal", svc_id, loc_id), svc_id, loc_id))
        cur.execute("""INSERT OR IGNORE INTO service_area (id,service_id,extent_type,fips,description)
                       VALUES (?,?,?,?,?)""", (sid("sa", svc_id, fips), svc_id, "county", fips, "Site county"))
        if phone:
            cur.execute("INSERT OR REPLACE INTO phone (id,organization_id,number,type) VALUES (?,?,?,?)",
                        (sid("ph", org_id), org_id, phone, "voice"))
        if hours:
            cur.execute("INSERT OR REPLACE INTO schedule (id,service_id,description) VALUES (?,?,?)",
                        (sid("sch", svc_id), svc_id, hours))
        cur.execute("""INSERT OR REPLACE INTO record_provenance
            (id,record_table,record_id,source_id,source_url,date_checked,confidence,extracted_by,method)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (sid("prov", org_id), "organization", org_id, SOURCE_ID, SITE_URL, TODAY,
             CONFIDENCE, "automated", "api_pull"))
        stats["loaded"] += 1

    if not dry_run:
        cur.execute("""INSERT INTO refresh_log
            (id,run_started,run_finished,refresh_quarter,source_id,stage,status,records_in,records_out,records_rejected,message)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (sid("run", SOURCE_ID, TODAY), TODAY, TODAY, "2026Q2", SOURCE_ID, "load", "success",
             stats["in"], stats["loaded"], stats["rejected_pii"],
             f"out_of_area={stats['out_of_area']} no_geo={stats['no_geo']}"))
        con.commit()
    con.close()
    return stats

def main():
    dry = "--dry-run" in sys.argv
    print("[ofs-metro] fetching store_search ...")
    rows = fetch_rows()
    print(f"[ofs-metro] {len(rows)} locations. {'DRY RUN' if dry else 'loading'} (geocoding each) ...")
    s = load(rows, dry_run=dry)
    print(f"[ofs-metro] loaded={s['loaded']} out_of_area(IL etc)={s['out_of_area']} "
          f"no_geo={s['no_geo']} pii_rejected={s['rejected_pii']}")

if __name__ == "__main__":
    main()
