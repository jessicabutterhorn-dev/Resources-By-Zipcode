#!/usr/bin/env python3
"""Open-route connector: data.mo.gov (Missouri Open Data, Socrata SODA API).

Proves the full pipeline path end-to-end with REAL public data:
  ingest -> normalize (HSDS) -> geocode (Census) -> verify (PII tripwire +
  provenance) -> load (SQLite). Run build_frontend.py afterwards to publish.

Dataset: kuz5-m96r  "Missouri Job Centers / Works Assistance Locations"
  Statewide workforce + benefit-navigation offices (name, phone, address,
  hours, lat/long). Mapped to resource_bucket='navigation'.

SAFE-ROUTE compliance enforced here:
  * Uses the public SODA API (not scraping). robots.txt allows /resource/
    (only /browse?* UI facets are disallowed); Crawl-delay: 1 honored.
  * Polite: descriptive User-Agent, paginated, sleeps between requests.
  * Facts only — name/phone/address/hours. No prose reproduced.
  * Public/open license (Socrata) -> attribution rendered on the page.
  * Every record gets source_url + date_checked + confidence + a
    record_provenance row.
  * PII tripwire rejects any member-shaped field before load.

Stdlib only (urllib) — no third-party deps.

Usage:  python3 pipeline/connectors/data_mo_gov.py            # load into db/resources.db
        python3 pipeline/connectors/data_mo_gov.py --dry-run  # fetch+normalize, no DB write
"""
import json, os, re, sqlite3, sys, time, hashlib, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "db", "resources.db")
ZONES_JSON = os.path.join(ROOT, "data", "zones.json")
RAW_DIR = os.path.join(ROOT, "data", "raw", "data_mo_gov")

UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
SODA_BASE = "https://data.mo.gov/resource/kuz5-m96r.json"
DATASET_URL = "https://data.mo.gov/d/kuz5-m96r"
CENSUS_GEO = ("https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
              "?benchmark=Public_AR_Current&vintage=Current_Current&format=json&layers=Counties")
CRAWL_DELAY = 1.0          # honor robots.txt Crawl-delay: 1
CENSUS_DELAY = 0.5
PAGE = 1000

SOURCE_ID = "data-mo-gov"
TODAY = "2026-06-24"        # date_checked (pass-through; pipeline stamps real run date)
CONFIDENCE = "medium"      # single official/open feed (verify ladder)

# PII tripwire: any record key/value matching these = reject (no member data allowed)
PII_KEY_PAT = re.compile(r"\b(ssn|social.?security|dob|date.?of.?birth|member.?id|"
                         r"medicare.?id|mbi|beneficiary|claim|diagnosis|patient)\b", re.I)
PII_VAL_PAT = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")   # SSN-shaped

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def sid(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:24]

# ---- 1. INGEST -------------------------------------------------------------
def fetch_rows():
    rows, offset = [], 0
    while True:
        url = f"{SODA_BASE}?$limit={PAGE}&$offset={offset}&$order=:id"
        batch = _get(url)
        rows.extend(batch)
        if len(batch) < PAGE:
            break
        offset += PAGE
        time.sleep(CRAWL_DELAY)
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(os.path.join(RAW_DIR, f"kuz5-m96r_{TODAY}.json"), "w") as f:
        json.dump(rows, f, indent=1)
    return rows

# ---- PII tripwire ----------------------------------------------------------
def pii_reject(row):
    for k, v in row.items():
        if PII_KEY_PAT.search(str(k)):
            return f"forbidden key '{k}'"
        if isinstance(v, str) and PII_VAL_PAT.search(v):
            return f"SSN-shaped value in '{k}'"
    return None

# ---- zone resolver (county name+state -> zone) -----------------------------
def norm(name):
    return re.sub(r"[^a-z ]", "", name.lower()).replace(" county", "").strip()

def load_zone_resolver():
    z = json.load(open(ZONES_JSON))
    resolver = {}
    for zone in z["zones"]:
        for st, counties in zone["counties"].items():
            for cty in counties:
                resolver[(st, norm(cty))] = zone["zone_id"]
    return resolver

# ---- 3. GEOCODE (Census coordinates -> county FIPS) ------------------------
def geocode_county(lat, lon):
    try:
        url = f"{CENSUS_GEO}&x={lon}&y={lat}"
        d = _get(url)
        cs = d["result"]["geographies"]["Counties"]
        if not cs:
            return None
        c = cs[0]
        fips = c["GEOID"]                    # 5-digit state+county
        name = "St. Louis City" if fips == "29510" else c["BASENAME"]
        state = {"29": "MO", "20": "KS"}.get(fips[:2])
        return {"fips": fips, "county_name": name, "state": state}
    except Exception as e:
        sys.stderr.write(f"  geocode fail ({lat},{lon}): {e}\n")
        return None

# ---- 2. NORMALIZE to HSDS --------------------------------------------------
def normalize(row):
    """One data.mo.gov row -> nested HSDS dict (org/location/address/service/phone/schedule)."""
    name = (row.get("center") or "").strip()
    if not name:
        return None
    loc = row.get("location_1") or {}
    ha = {}
    if loc.get("human_address"):
        try: ha = json.loads(loc["human_address"])
        except Exception: ha = {}
    lat = loc.get("latitude"); lon = loc.get("longitude")
    phones = [p for p in [row.get("phone_number"), row.get("phone_number_2")] if p]
    hours = (row.get("additional_information") or "").strip() or None
    addr1 = (ha.get("address") or "").strip() or None
    addr2 = (row.get("address_2") or "").strip() or None

    org_id = sid("mo-jobcenter", name)
    return {
        "org_id": org_id,
        "org_name": name,
        "loc_id": sid("loc", org_id),
        "lat": float(lat) if lat else None,
        "lon": float(lon) if lon else None,
        "addr1": addr1, "addr2": addr2,
        "city": (ha.get("city") or "").strip() or None,
        "state": (ha.get("state") or "").strip() or None,
        "zip": (ha.get("zip") or "").strip() or None,
        "svc_id": sid("svc", org_id),
        "svc_name": "Missouri Job Center — workforce & benefit navigation",
        "phones": phones,
        "hours": hours,
    }

# ---- source + geography upserts --------------------------------------------
def ensure_source(cur):
    cur.execute("""INSERT OR REPLACE INTO source
        (id, source_name, source_type, publisher, source_url, robots_checked,
         license, attribution_text, attribution_required, redistribution_ok,
         access_route, refresh_mode, date_checked, confidence, notes)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (SOURCE_ID, "State of Missouri Open Data (data.mo.gov) — Job Centers",
         "gov_open_data", "State of Missouri", DATASET_URL, 1,
         "open-Socrata", "Source: State of Missouri Open Data (data.mo.gov)", 1, 1,
         "open", "live_api", TODAY, CONFIDENCE,
         "Dataset kuz5-m96r. SODA API. robots.txt /resource allowed, Crawl-delay 1 honored."))

def ensure_geo(cur, geo, resolver, seen_county, seen_zip_county):
    fips, name, state = geo["fips"], geo["county_name"], geo["state"]
    zone_id = resolver.get((state, norm(name)))
    if zone_id is None:
        return None
    if fips not in seen_county:
        cur.execute("INSERT OR IGNORE INTO county (fips, county_name, state, is_independent_city) VALUES (?,?,?,?)",
                    (fips, name, state, 1 if fips == "29510" else 0))
        cur.execute("INSERT OR IGNORE INTO zone (zone_id, zone_name) "
                    "SELECT ?, ? WHERE NOT EXISTS (SELECT 1 FROM zone WHERE zone_id=?)",
                    (zone_id, f"Zone {zone_id}", zone_id))
        cur.execute("INSERT OR IGNORE INTO county_zone (fips, zone_id) VALUES (?,?)", (fips, zone_id))
        seen_county.add(fips)
    return {"fips": fips, "zone_id": zone_id}

# ---- 4+5. VERIFY + LOAD ----------------------------------------------------
def load(rows, dry_run=False):
    resolver = load_zone_resolver()
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()
    if not dry_run:
        ensure_source(cur)

    seen_county, seen_zip = set(), set()
    stats = {"in": len(rows), "rejected_pii": 0, "no_geo": 0, "no_zone": 0, "loaded": 0}

    for row in rows:
        why = pii_reject(row)
        if why:
            stats["rejected_pii"] += 1
            sys.stderr.write(f"  PII tripwire rejected a row: {why}\n")
            continue
        rec = normalize(row)
        if not rec:
            continue
        if rec["lat"] is None or rec["lon"] is None:
            stats["no_geo"] += 1
            continue

        geo = geocode_county(rec["lat"], rec["lon"])
        time.sleep(CENSUS_DELAY)
        if not geo or not geo["state"]:
            stats["no_geo"] += 1
            continue
        gz = None if dry_run else ensure_geo(cur, geo, resolver, seen_county, seen_zip)
        zone_id = (gz or {}).get("zone_id") if not dry_run else resolver.get((geo["state"], norm(geo["county_name"])))
        if zone_id is None:
            stats["no_zone"] += 1
            continue

        if dry_run:
            stats["loaded"] += 1
            print(f"  OK  {rec['org_name'][:42]:42}  {rec['city']},{geo['state']} {rec['zip']}  -> {geo['county_name']} (zone {zone_id})")
            continue

        # zip -> county crosswalk learned from this record
        if rec["zip"] and (rec["zip"], geo["fips"]) not in seen_zip:
            pass  # zip_county via load_zip_county.py (Census crosswalk)
            seen_zip.add((rec["zip"], geo["fips"]))

        # organization
        cur.execute("""INSERT OR REPLACE INTO organization
            (id,name,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?)""",
            (rec["org_id"], rec["org_name"], SOURCE_ID, DATASET_URL, TODAY, CONFIDENCE))
        # location
        cur.execute("""INSERT OR REPLACE INTO location
            (id,organization_id,name,location_type,latitude,longitude,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (rec["loc_id"], rec["org_id"], rec["org_name"], "physical", rec["lat"], rec["lon"],
             SOURCE_ID, DATASET_URL, TODAY, CONFIDENCE))
        # address (carries geocoded fips + zone)
        cur.execute("""INSERT OR REPLACE INTO address
            (id,location_id,address_1,address_2,city,state_province,postal_code,fips,zone_id)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (sid("addr", rec["loc_id"]), rec["loc_id"], rec["addr1"], rec["addr2"],
             rec["city"], geo["state"], rec["zip"], geo["fips"], zone_id))
        # service
        cur.execute("""INSERT OR REPLACE INTO service
            (id,organization_id,name,resource_bucket,status,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (rec["svc_id"], rec["org_id"], rec["svc_name"], "navigation", "active",
             SOURCE_ID, DATASET_URL, TODAY, CONFIDENCE))
        cur.execute("INSERT OR IGNORE INTO service_at_location (id,service_id,location_id) VALUES (?,?,?)",
                    (sid("sal", rec["svc_id"], rec["loc_id"]), rec["svc_id"], rec["loc_id"]))
        # phones
        for i, ph in enumerate(rec["phones"]):
            cur.execute("INSERT OR REPLACE INTO phone (id,organization_id,number,type) VALUES (?,?,?,?)",
                        (sid("ph", rec["org_id"], i), rec["org_id"], ph, "voice"))
        # hours
        if rec["hours"]:
            cur.execute("INSERT OR REPLACE INTO schedule (id,service_id,description) VALUES (?,?,?)",
                        (sid("sch", rec["svc_id"]), rec["svc_id"], rec["hours"]))
        # provenance (multi-source corroboration support)
        cur.execute("""INSERT OR REPLACE INTO record_provenance
            (id,record_table,record_id,source_id,source_url,date_checked,confidence,extracted_by,method)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (sid("prov", rec["org_id"]), "organization", rec["org_id"], SOURCE_ID,
             DATASET_URL, TODAY, CONFIDENCE, "automated", "api_pull"))
        stats["loaded"] += 1

    if not dry_run:
        cur.execute("""INSERT INTO refresh_log
            (id,run_started,run_finished,refresh_quarter,source_id,stage,status,records_in,records_out,records_rejected,message)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (sid("run", SOURCE_ID, TODAY), TODAY, TODAY, "2026Q2", SOURCE_ID, "load", "success",
             stats["in"], stats["loaded"], stats["rejected_pii"],
             f"no_geo={stats['no_geo']} no_zone={stats['no_zone']}"))
        con.commit()
    con.close()
    return stats

def main():
    dry = "--dry-run" in sys.argv
    print(f"[data.mo.gov] fetching kuz5-m96r ...")
    rows = fetch_rows()
    print(f"[data.mo.gov] {len(rows)} rows fetched. {'DRY RUN' if dry else 'loading'} ...")
    stats = load(rows, dry_run=dry)
    print(f"[data.mo.gov] in={stats['in']} loaded={stats['loaded']} "
          f"pii_rejected={stats['rejected_pii']} no_geo={stats['no_geo']} no_zone={stats['no_zone']}")

if __name__ == "__main__":
    main()
