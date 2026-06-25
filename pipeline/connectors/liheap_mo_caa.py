#!/usr/bin/env python3
"""Open-route connector: Missouri LIHEAP / energy-assistance via Community Action Agencies.

Missouri delivers LIHEAP (Low Income Home Energy Assistance Program) through
Community Action Agencies (CAAs). This connector pulls the state's CAA directory
and loads their energy/utility (+ food, housing) services.

Source: data.mo.gov dataset wn56-7gv3 "CAA Contact Info Websites Services"
  (Socrata SODA API). Each CAA has name, hours, website, serving_counties
  (a REGION — modeled as HSDS service_area), services_provided, geocoded address.

Path: ingest -> normalize (HSDS, incl. service_area per served county) ->
geocode office (Census coords -> FIPS) -> verify (PII tripwire + provenance)
-> load SQLite.

SAFE-ROUTE: SODA API (not scraping); open-Socrata license + attribution;
facts only; no eligibility fabricated (dataset has none); source_url +
date_checked + confidence + provenance per record; PII tripwire.

NOTE: dataset has NO phone field -> phone omitted (website + hours + address
captured instead). Requires pipeline/load_geography.py to have run first
(needs the county name->FIPS reference).

Stdlib only.
"""
import json, os, re, sqlite3, sys, time, hashlib, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "db", "resources.db")
RAW_DIR = os.path.join(ROOT, "data", "raw", "liheap_mo_caa")

UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
SODA_BASE = "https://data.mo.gov/resource/wn56-7gv3.json"
DATASET_URL = "https://data.mo.gov/d/wn56-7gv3"
CENSUS_GEO = ("https://geocoding.geo.census.gov/geocoder/geographies/coordinates"
              "?benchmark=Public_AR_Current&vintage=Current_Current&format=json&layers=Counties")
CENSUS_DELAY = 0.5
SOURCE_ID = "data-mo-gov-caa"
TODAY = "2026-06-24"
CONFIDENCE = "medium"

PII_KEY_PAT = re.compile(r"\b(ssn|social.?security|dob|date.?of.?birth|member.?id|"
                         r"medicare.?id|mbi|beneficiary|claim|diagnosis|patient)\b", re.I)
PII_VAL_PAT = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

# services_provided text -> resource buckets (keyword map)
BUCKET_RULES = [
    ("utility",  ["energy", "liheap", "utilit", "weatheriz"]),
    ("food",     ["food"]),
    ("housing",  ["housing", "homeless", "shelter", "rent"]),
    ("gas_transport", ["transport"]),
]
BUCKET_SVC_NAME = {
    "utility": "Energy / Utility Assistance (LIHEAP)",
    "food": "Food Pantry",
    "housing": "Housing / Homeless Assistance",
    "gas_transport": "Transportation Assistance",
}

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))

def sid(*p):
    return hashlib.sha1("|".join(str(x) for x in p).encode()).hexdigest()[:24]

def norm(name):
    return re.sub(r"[^a-z ]", "", name.lower()).replace(" county", "").strip()

def pii_reject(row):
    for k, v in row.items():
        if PII_KEY_PAT.search(str(k)):
            return f"forbidden key '{k}'"
        if isinstance(v, str) and PII_VAL_PAT.search(v):
            return f"SSN-shaped value in '{k}'"
    return None

def fetch_rows():
    rows = _get(f"{SODA_BASE}?$limit=1000&$order=:id")
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(os.path.join(RAW_DIR, f"wn56-7gv3_{TODAY}.json"), "w") as f:
        json.dump(rows, f, indent=1)
    return rows

def geocode_county(lat, lon):
    try:
        d = _get(f"{CENSUS_GEO}&x={lon}&y={lat}")
        cs = d["result"]["geographies"]["Counties"]
        if not cs:
            return None
        c = cs[0]
        fips = c["GEOID"]
        return {"fips": fips, "state": {"29": "MO", "20": "KS"}.get(fips[:2])}
    except Exception as e:
        sys.stderr.write(f"  geocode fail ({lat},{lon}): {e}\n")
        return None

def parse_buckets(services_text):
    t = (services_text or "").lower()
    found = []
    for bucket, kws in BUCKET_RULES:
        if any(kw in t for kw in kws):
            found.append(bucket)
    return found or ["navigation"]

def resolve_counties(raw, name2fips):
    """Resolve serving_counties text -> set of MO FIPS.

    Split on commas first (preserves multi-word counties like 'St. Louis',
    'Cape Girardeau'). Only if a comma-piece doesn't match do we fall back to
    token-splitting it (handles rare missing-comma data like 'Knox Schuyler')."""
    fipset, unmatched = set(), 0
    for piece in (raw or "").split(","):
        p = piece.strip()
        if not p:
            continue
        f = name2fips.get(("MO", norm(p)))
        if f:
            fipset.add(f)
            continue
        matched = False
        for tok in p.split():                     # missing-comma fallback
            f2 = name2fips.get(("MO", norm(tok)))
            if f2:
                fipset.add(f2)
                matched = True
        if not matched:
            unmatched += 1
    return fipset, unmatched

def load(rows, dry_run=False):
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    # county name -> fips lookup (MO) from the geography spine
    name2fips = {}
    for fips, cname, state in cur.execute("SELECT fips, county_name, state FROM county"):
        name2fips[(state, norm(cname))] = fips

    if not dry_run:
        cur.execute("""INSERT OR REPLACE INTO source
            (id, source_name, source_type, publisher, source_url, robots_checked,
             license, attribution_text, attribution_required, redistribution_ok,
             access_route, refresh_mode, date_checked, confidence, notes)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (SOURCE_ID, "State of Missouri Open Data (data.mo.gov) — Community Action Agencies",
             "gov_open_data", "State of Missouri", DATASET_URL, 1,
             "open-Socrata", "Source: State of Missouri Open Data (data.mo.gov)", 1, 1,
             "open", "live_api", TODAY, CONFIDENCE,
             "Dataset wn56-7gv3. MO LIHEAP delivered via CAAs. SODA API; facts only."))

    stats = {"in": len(rows), "rejected_pii": 0, "no_geo": 0, "agencies": 0,
             "services": 0, "service_areas": 0, "county_unmatched": 0}

    for row in rows:
        why = pii_reject(row)
        if why:
            stats["rejected_pii"] += 1
            continue
        name = (row.get("community_action_agency") or "").strip()
        if not name:
            continue
        loc = row.get("location_1") or {}
        ha = {}
        if loc.get("human_address"):
            try: ha = json.loads(loc["human_address"])
            except Exception: ha = {}
        lat, lon = loc.get("latitude"), loc.get("longitude")
        if not lat or not lon:
            stats["no_geo"] += 1
            continue
        geo = geocode_county(float(lat), float(lon))
        time.sleep(CENSUS_DELAY)
        if not geo:
            stats["no_geo"] += 1
            continue

        # resolve served counties (region) -> fips set (+ office county)
        served_fips, unmatched = resolve_counties(row.get("serving_counties"), name2fips)
        served_fips.add(geo["fips"])
        stats["county_unmatched"] += unmatched

        buckets = parse_buckets(row.get("services_provided"))
        website = (row.get("website_link") or "").strip() or None
        hours = (row.get("office_hours_excludes_holidays") or "").strip() or None
        addr1 = (ha.get("address") or "").strip() or None
        city = (ha.get("city") or "").strip() or None
        zipc = (ha.get("zip") or "").strip() or None

        org_id = sid("mo-caa", name)
        loc_id = sid("loc", org_id)

        if dry_run:
            print(f"  OK {name[:38]:38} {city},MO {zipc}  buckets={','.join(buckets)}  "
                  f"serves {len(served_fips)} counties")
            stats["agencies"] += 1
            stats["services"] += len(buckets)
            stats["service_areas"] += len(served_fips) * len(buckets)
            continue

        # org + location + address (office) + provenance
        cur.execute("""INSERT OR REPLACE INTO organization
            (id,name,website,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?)""",
            (org_id, name, website, SOURCE_ID, DATASET_URL, TODAY, CONFIDENCE))
        cur.execute("""INSERT OR REPLACE INTO location
            (id,organization_id,name,location_type,latitude,longitude,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (loc_id, org_id, name, "physical", float(lat), float(lon),
             SOURCE_ID, DATASET_URL, TODAY, CONFIDENCE))
        cur.execute("""INSERT OR REPLACE INTO address
            (id,location_id,address_1,city,state_province,postal_code,fips,zone_id)
            VALUES (?,?,?,?,?,?,?, (SELECT zone_id FROM county_zone WHERE fips=?))""",
            (sid("addr", loc_id), loc_id, addr1, city, "MO", zipc, geo["fips"], geo["fips"]))
        if zipc:
            cur.execute("""INSERT OR IGNORE INTO zip_county (zip,fips,is_primary,crosswalk_vintage,source_id)
                           VALUES (?,?,1,?,?)""", (zipc, geo["fips"], "census-derived", SOURCE_ID))
        cur.execute("""INSERT OR REPLACE INTO record_provenance
            (id,record_table,record_id,source_id,source_url,date_checked,confidence,extracted_by,method)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (sid("prov", org_id), "organization", org_id, SOURCE_ID, DATASET_URL, TODAY,
             CONFIDENCE, "automated", "api_pull"))
        stats["agencies"] += 1

        # one service per detected bucket, each covering the full served region
        for bucket in buckets:
            svc_id = sid("svc", org_id, bucket)
            cur.execute("""INSERT OR REPLACE INTO service
                (id,organization_id,name,resource_bucket,status,source_id,source_url,date_checked,confidence)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (svc_id, org_id, BUCKET_SVC_NAME.get(bucket, bucket), bucket, "active",
                 SOURCE_ID, DATASET_URL, TODAY, CONFIDENCE))
            cur.execute("INSERT OR IGNORE INTO service_at_location (id,service_id,location_id) VALUES (?,?,?)",
                        (sid("sal", svc_id, loc_id), svc_id, loc_id))
            if hours:
                cur.execute("INSERT OR REPLACE INTO schedule (id,service_id,description) VALUES (?,?,?)",
                            (sid("sch", svc_id), svc_id, hours))
            for f in served_fips:
                cur.execute("""INSERT OR IGNORE INTO service_area (id,service_id,extent_type,fips,description)
                               VALUES (?,?,?,?,?)""",
                            (sid("sa", svc_id, f), svc_id, "county", f, "Served county (CAA region)"))
                stats["service_areas"] += 1
            stats["services"] += 1

    if not dry_run:
        cur.execute("""INSERT INTO refresh_log
            (id,run_started,run_finished,refresh_quarter,source_id,stage,status,records_in,records_out,records_rejected,message)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (sid("run", SOURCE_ID, TODAY), TODAY, TODAY, "2026Q2", SOURCE_ID, "load", "success",
             stats["in"], stats["agencies"], stats["rejected_pii"],
             f"services={stats['services']} service_areas={stats['service_areas']} "
             f"county_unmatched={stats['county_unmatched']} no_geo={stats['no_geo']}"))
        con.commit()
    con.close()
    return stats

def main():
    dry = "--dry-run" in sys.argv
    print("[liheap-mo-caa] fetching wn56-7gv3 ...")
    rows = fetch_rows()
    print(f"[liheap-mo-caa] {len(rows)} agencies fetched. {'DRY RUN' if dry else 'loading'} ...")
    s = load(rows, dry_run=dry)
    print(f"[liheap-mo-caa] agencies={s['agencies']} services={s['services']} "
          f"service_areas={s['service_areas']} pii_rejected={s['rejected_pii']} "
          f"no_geo={s['no_geo']} county_unmatched={s['county_unmatched']}")

if __name__ == "__main__":
    main()
