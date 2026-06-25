#!/usr/bin/env python3
"""Open-route connector: HUD Single-Family Housing Counseling Agencies (KS + MO).

HUD-certified nonprofits that provide free/low-cost help with rent, housing,
foreclosure prevention, and budgeting — relevant for members needing housing /
rent assistance. This is the first KANSAS source (KS has no Socrata portal);
it also adds Missouri agencies.

Source: HUD Official Content ArcGIS Feature Service
  "Single_Family_Housing_Counseling_Agencies" (public domain, US Gov).
  Each record has name, address, city, state, ZIP, phone, email, website,
  and county FIPS (STATE2KX + CURCNTY) -> NO geocoding needed.

Path: ingest (ArcGIS REST, paginated) -> normalize (HSDS) -> verify (PII
tripwire + provenance) -> load. County FIPS comes from the data, mapped to a
zone via the geography spine (run load_geography.py first).

SAFE-ROUTE: official ArcGIS REST API (not scraping); US-Gov public domain;
facts only; source_url + date_checked + confidence + provenance per record.

Stdlib only.
"""
import json, os, re, sqlite3, sys, time, hashlib, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "db", "resources.db")
RAW_DIR = os.path.join(ROOT, "data", "raw", "hud_housing_counseling")

UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
SERVICE = ("https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/"
           "Single_Family_Housing_Counseling_Agencies/FeatureServer/0/query")
ITEM_URL = "https://www.arcgis.com/home/item.html?id=aad167f1d819436bb8b539d762716959"
PAGE = 1000
PAGE_DELAY = 0.5
SOURCE_ID = "hud-housing-counseling"
TODAY = "2026-06-24"
CONFIDENCE = "medium"
ALL_STATE_FIPS = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
    "08": "CO", "09": "CT", "10": "DE", "11": "DC", "12": "FL",
    "13": "GA", "15": "HI", "16": "ID", "17": "IL", "18": "IN",
    "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME",
    "24": "MD", "25": "MA", "26": "MI", "27": "MN", "28": "MS",
    "29": "MO", "30": "MT", "31": "NE", "32": "NV", "33": "NH",
    "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
    "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI",
    "45": "SC", "46": "SD", "47": "TN", "48": "TX", "49": "UT",
    "50": "VT", "51": "VA", "53": "WA", "54": "WV", "55": "WI",
    "56": "WY", "72": "PR",
}
FIPS_BY_STATE = {v: k for k, v in ALL_STATE_FIPS.items()}

OUT_FIELDS = ("AGC_NAME,AGC_ADDRESS,AGC_CITY,AGC_ZIP_CODE,AGC_PHONE_NBR,"
              "AGC_EMAIL,AGC_WEB_SITE,STATE2KX,CURCNTY,CURCNTY_NM")
PII_KEY_PAT = re.compile(r"\b(ssn|social.?security|dob|date.?of.?birth|member.?id|"
                         r"medicare.?id|mbi|beneficiary|claim|diagnosis|patient)\b", re.I)
PII_VAL_PAT = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode("utf-8"))

def sid(*p):
    return hashlib.sha1("|".join(str(x) for x in p).encode()).hexdigest()[:24]

def titlecase(s):
    return re.sub(r"\b\w+\b", lambda m: m.group(0).capitalize(), s) if s else s

def pii_reject(attrs):
    for k, v in attrs.items():
        if PII_KEY_PAT.search(str(k)):
            return f"forbidden key '{k}'"
        if isinstance(v, str) and PII_VAL_PAT.search(v):
            return f"SSN-shaped value in '{k}'"
    return None

def fetch_rows(states_set):
    rows, offset = [], 0
    fp_list = sorted(FIPS_BY_STATE[s] for s in states_set if s in FIPS_BY_STATE)
    if not fp_list:
        sys.exit(f"[hud-hca] No known FIPS codes for: {states_set}")
    in_clause = ",".join(f"'{f}'" for f in fp_list)
    where = urllib.parse.quote(f"STATE2KX IN ({in_clause})")
    while True:
        url = (f"{SERVICE}?where={where}&outFields={urllib.parse.quote(OUT_FIELDS)}"
               f"&returnGeometry=true&outSR=4326&f=json"
               f"&resultOffset={offset}&resultRecordCount={PAGE}")
        d = _get(url)
        feats = d.get("features", [])
        rows.extend(feats)
        if not d.get("exceededTransferLimit") or not feats:
            break
        offset += PAGE
        time.sleep(PAGE_DELAY)
    os.makedirs(RAW_DIR, exist_ok=True)
    with open(os.path.join(RAW_DIR, f"hud_hca_{TODAY}.json"), "w") as f:
        json.dump(rows, f, indent=1)
    return rows

def load(rows, states_set, dry_run=False):
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
            (SOURCE_ID, "HUD Single-Family Housing Counseling Agencies",
             "gov_open_data", "U.S. Dept of Housing and Urban Development", ITEM_URL, 1,
             "US-Gov-PublicDomain", "Source: U.S. Department of Housing and Urban Development",
             0, 1, "open", "live_api", TODAY, CONFIDENCE,
             "HUD Official Content ArcGIS Feature Service. County FIPS in data; no geocoding."))

    stats = {"in": len(rows), "rejected_pii": 0, "no_county": 0, "loaded": 0}
    state_counts = {s: 0 for s in states_set}
    for ft in rows:
        a = ft.get("attributes", {})
        if pii_reject(a):
            stats["rejected_pii"] += 1
            continue
        name = titlecase((a.get("AGC_NAME") or "").strip())
        if not name:
            continue
        statefp = (a.get("STATE2KX") or "").strip()
        cnty = (a.get("CURCNTY") or "").strip()
        fips = statefp + cnty if statefp and cnty else None
        state = ALL_STATE_FIPS.get(statefp)
        if not fips or fips not in known_fips or not state or state not in states_set:
            stats["no_county"] += 1
            continue

        zipc = (a.get("AGC_ZIP_CODE") or "").split("-")[0].strip() or None
        phone = (a.get("AGC_PHONE_NBR") or "").strip() or None
        email = (a.get("AGC_EMAIL") or "").strip() or None
        web = (a.get("AGC_WEB_SITE") or "").strip() or None
        addr1 = titlecase((a.get("AGC_ADDRESS") or "").strip()) or None
        city = titlecase((a.get("AGC_CITY") or "").strip()) or None
        geom = ft.get("geometry") or {}
        lat, lon = geom.get("y"), geom.get("x")

        state_counts[state] = state_counts.get(state, 0) + 1
        if dry_run:
            print(f"  OK {name[:38]:38} {city},{state} {zipc}  {a.get('CURCNTY_NM')} ({fips})  {phone or web or ''}")
            stats["loaded"] += 1
            continue

        org_id = sid("hud-hca", name, city, zipc)
        loc_id = sid("loc", org_id)
        svc_id = sid("svc", org_id)

        cur.execute("""INSERT OR REPLACE INTO organization
            (id,name,email,website,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?)""",
            (org_id, name, email, web, SOURCE_ID, ITEM_URL, TODAY, CONFIDENCE))
        cur.execute("""INSERT OR REPLACE INTO location
            (id,organization_id,name,location_type,latitude,longitude,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (loc_id, org_id, name, "physical", lat, lon, SOURCE_ID, ITEM_URL, TODAY, CONFIDENCE))
        cur.execute("""INSERT OR REPLACE INTO address
            (id,location_id,address_1,city,state_province,postal_code,fips,zone_id)
            VALUES (?,?,?,?,?,?,?, (SELECT zone_id FROM county_zone WHERE fips=?))""",
            (sid("addr", loc_id), loc_id, addr1, city, state, zipc, fips, fips))
        if zipc:
            pass  # zip_county via load_zip_county.py (Census crosswalk)
        cur.execute("""INSERT OR REPLACE INTO service
            (id,organization_id,name,resource_bucket,status,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (svc_id, org_id, "HUD-approved housing counseling", "housing", "active",
             SOURCE_ID, ITEM_URL, TODAY, CONFIDENCE))
        cur.execute("INSERT OR IGNORE INTO service_at_location (id,service_id,location_id) VALUES (?,?,?)",
                    (sid("sal", svc_id, loc_id), svc_id, loc_id))
        cur.execute("""INSERT OR IGNORE INTO service_area (id,service_id,extent_type,fips,description)
                       VALUES (?,?,?,?,?)""",
                    (sid("sa", svc_id, fips), svc_id, "county", fips, "Office county"))
        if phone:
            cur.execute("INSERT OR REPLACE INTO phone (id,organization_id,number,type) VALUES (?,?,?,?)",
                        (sid("ph", org_id), org_id, phone, "voice"))
        cur.execute("""INSERT OR REPLACE INTO record_provenance
            (id,record_table,record_id,source_id,source_url,date_checked,confidence,extracted_by,method)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (sid("prov", org_id), "organization", org_id, SOURCE_ID, ITEM_URL, TODAY,
             CONFIDENCE, "automated", "api_pull"))
        stats["loaded"] += 1

    if not dry_run:
        cur.execute("""INSERT INTO refresh_log
            (id,run_started,run_finished,refresh_quarter,source_id,stage,status,records_in,records_out,records_rejected,message)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (sid("run", SOURCE_ID, TODAY), TODAY, TODAY, "2026Q2", SOURCE_ID, "load", "success",
             stats["in"], stats["loaded"], stats["rejected_pii"],
             " ".join(f"{s.lower()}={state_counts.get(s,0)}" for s in sorted(states_set)) +
             f" no_county={stats['no_county']}"))
        con.commit()
    con.close()
    stats["state_counts"] = state_counts
    return stats

def main():
    states_set = set(sys.argv[sys.argv.index("--states") + 1].upper().split(",")) if "--states" in sys.argv else {"KS", "MO"}
    dry = "--dry-run" in sys.argv
    print(f"[hud-hca] fetching HUD housing counseling agencies ({','.join(sorted(states_set))}) ...")
    rows = fetch_rows(states_set)
    print(f"[hud-hca] {len(rows)} rows fetched. {'DRY RUN' if dry else 'loading'} ...")
    s = load(rows, states_set, dry_run=dry)
    sc = s.get("state_counts", {})
    print(f"[hud-hca] loaded={s['loaded']} ({' '.join(f'{k}={v}' for k,v in sorted(sc.items()))}) "
          f"pii_rejected={s['rejected_pii']} no_county={s['no_county']}")

if __name__ == "__main__":
    main()
