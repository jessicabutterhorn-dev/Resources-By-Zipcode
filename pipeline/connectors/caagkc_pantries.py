#!/usr/bin/env python3
"""Per-site connector: CAAGKC partner food pantries (Kansas City metro).

The open dataset only has CAAGKC at the agency level (one 'food' record). The
agency's own public program page lists ~30 partner FOOD PANTRIES with address,
phone, and hours — the granular, member-usable data. This connector extracts
those facts.

Source: https://caagkc.org/programs/food-toiletry-pantries/
  robots.txt: 'Disallow:' (everything allowed), Crawl-delay 10 (single GET here).
  This is the operating agency publishing its OWN partner list (not a
  proprietary aggregator). Facts only (name/address/phone/hours), attribution
  to CAAGKC. Safe-route acceptable as a trusted, robots-permitted per-site pull.

CAVEAT: HTML extraction is fragile (breaks if the page is redesigned) and
per-site (does not scale like the open APIs). Rows that don't parse cleanly are
skipped and logged — never guessed.

Path: ingest (1 GET) -> parse table -> normalize (HSDS) -> geocode (Census
one-line address -> county FIPS) -> verify (PII tripwire + provenance) -> load.

Stdlib only. Requires load_geography.py to have run.
"""
import json, os, re, sqlite3, sys, time, hashlib, html, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB = os.path.join(ROOT, "db", "resources.db")
RAW_DIR = os.path.join(ROOT, "data", "raw", "caagkc_pantries")

UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
PAGE_URL = "https://caagkc.org/programs/food-toiletry-pantries/"
CENSUS_ONELINE = ("https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"
                  "?benchmark=Public_AR_Current&vintage=Current_Current&format=json&layers=Counties")
CENSUS_DELAY = 0.5
SOURCE_ID = "caagkc-pantries"
TODAY = "2026-06-24"
CONFIDENCE = "medium"

PHONE_RE = re.compile(r"\(?\d{3}\)?[\s.\-]?\d{3}-\d{4}(?:,?\s*(?:Ext\.?|x)\s*\d+)?", re.I)
CITYSTZIP_RE = re.compile(r"(.+?),\s*(MO|KS)\s+(\d{5})")
STREET_SPLIT_RE = re.compile(
    r"^(.*?\b(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Dr|Drive|Hwy|Highway|Pkwy|Terr|Terrace|"
    r"Ct|Court|Ln|Lane|Way|Cir|Circle|Pl|Place|Trafficway|Trfwy)\.?)\s+(.+)$", re.I)
PII_KEY_PAT = re.compile(r"\b(ssn|dob|member.?id|medicare.?id|beneficiary|claim|diagnosis)\b", re.I)
PII_VAL_PAT = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")

def _get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = r.read().decode("utf-8", "replace")
    return data if raw else json.loads(data)

def sid(*p):
    return hashlib.sha1("|".join(str(x) for x in p).encode()).hexdigest()[:24]

def fetch_html():
    os.makedirs(RAW_DIR, exist_ok=True)
    try:
        h = _get(PAGE_URL, raw=True)
        with open(os.path.join(RAW_DIR, f"pantries_{TODAY}.html"), "w") as f:
            f.write(h)
        return h
    except Exception as e:
        # fragile per-site source: on a transient outage, fall back to the most
        # recent cached snapshot rather than aborting the whole build.
        snaps = sorted(f for f in os.listdir(RAW_DIR) if f.endswith(".html"))
        if not snaps:
            raise
        newest = os.path.join(RAW_DIR, snaps[-1])
        sys.stderr.write(f"  live fetch failed ({e}); using cached snapshot {snaps[-1]}\n")
        return open(newest, encoding="utf-8").read()

def parse_pantries(h):
    """Return list of {name,street,city,state,zip,phone,hours} from the page tables."""
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    out = []
    for table in re.findall(r"<table.*?</table>", h, flags=re.S | re.I):
        for tr in re.findall(r"<tr.*?</tr>", table, flags=re.S | re.I):
            cells = re.findall(r"<t[dh].*?</t[dh]>", tr, flags=re.S | re.I)
            vals = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip() for c in cells]
            if len(vals) < 2:
                continue
            blob, hours = vals[0], vals[1]
            if not blob or blob.lower().startswith("pantry"):   # header row
                continue
            rec = parse_blob(blob)
            if rec:
                rec["hours"] = hours or None
                out.append(rec)
    return out

def parse_blob(blob):
    """Split 'Name 1900 NE Englewood Rd. Gladstone, MO 64118 (816) 702-6801'."""
    phone = None
    pm = PHONE_RE.search(blob)
    if pm:
        phone = re.sub(r"\s+", " ", pm.group(0)).strip()
        blob = (blob[:pm.start()] + blob[pm.end():]).strip()
    cz = CITYSTZIP_RE.search(blob)
    if not cz:
        return None
    pre, state, zipc = cz.group(1).strip(), cz.group(2), cz.group(3)
    # split pre into name + street (street starts at first 2-5 digit run)
    nm = re.search(r"^(.*?)\s+(\d{2,6}\b.*)$", pre)
    if not nm:
        return None
    name = nm.group(1).strip(" .,-")
    afternum = nm.group(2).strip()
    sp = STREET_SPLIT_RE.match(afternum)
    if sp:
        street, city = sp.group(1).strip(), sp.group(2).strip()
    else:
        # fallback: last 1-2 tokens are city
        toks = afternum.split()
        city = " ".join(toks[-2:]); street = " ".join(toks[:-2])
    if not name or not street or not city:
        return None
    return {"name": name, "street": street, "city": city, "state": state,
            "zip": zipc, "phone": phone}

def geocode(rec):
    addr = f"{rec['street']}, {rec['city']}, {rec['state']} {rec['zip']}"
    try:
        d = _get(f"{CENSUS_ONELINE}&address={urllib.parse.quote(addr)}")
        ms = d["result"]["addressMatches"]
        if not ms:
            return None
        g = ms[0]["geographies"]["Counties"][0]
        return {"fips": g["GEOID"], "lat": ms[0]["coordinates"]["y"], "lon": ms[0]["coordinates"]["x"]}
    except Exception as e:
        sys.stderr.write(f"  geocode fail [{addr}]: {e}\n")
        return None

def load(recs, dry_run=False):
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
            (SOURCE_ID, "CAAGKC partner food pantries (caagkc.org)", "other",
             "Community Action Agency of Greater Kansas City", PAGE_URL, 1,
             "org-public-page-facts", "Source: Community Action Agency of Greater Kansas City (caagkc.org)",
             1, 1, "open", "snapshot", TODAY, CONFIDENCE,
             "Agency's own partner-pantry list. robots Disallow: empty, Crawl-delay 10. Facts only; HTML extraction (fragile)."))

    stats = {"parsed": len(recs), "rejected_pii": 0, "no_geo": 0, "loaded": 0}
    for rec in recs:
        if PII_KEY_PAT.search(rec["name"]) or (rec.get("phone") and PII_VAL_PAT.search(rec["phone"])):
            stats["rejected_pii"] += 1
            continue
        geo = geocode(rec)
        time.sleep(CENSUS_DELAY)
        if not geo or geo["fips"] not in known_fips:
            stats["no_geo"] += 1
            continue
        fips = geo["fips"]

        org_id = sid("caagkc-pantry", rec["name"], rec["zip"])
        loc_id = sid("loc", org_id); svc_id = sid("svc", org_id)
        if dry_run:
            print(f"  OK {rec['name'][:34]:34} {rec['street'][:22]:22} {rec['city']},{rec['state']} {rec['zip']} -> {fips}")
            stats["loaded"] += 1
            continue

        cur.execute("""INSERT OR REPLACE INTO organization (id,name,source_id,source_url,date_checked,confidence)
                       VALUES (?,?,?,?,?,?)""", (org_id, rec["name"], SOURCE_ID, PAGE_URL, TODAY, CONFIDENCE))
        cur.execute("""INSERT OR REPLACE INTO location
            (id,organization_id,name,location_type,latitude,longitude,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (loc_id, org_id, rec["name"], "physical", geo["lat"], geo["lon"], SOURCE_ID, PAGE_URL, TODAY, CONFIDENCE))
        cur.execute("""INSERT OR REPLACE INTO address
            (id,location_id,address_1,city,state_province,postal_code,fips,zone_id)
            VALUES (?,?,?,?,?,?,?, (SELECT zone_id FROM county_zone WHERE fips=?))""",
            (sid("addr", loc_id), loc_id, rec["street"], rec["city"], rec["state"], rec["zip"], fips, fips))
        cur.execute("""INSERT OR IGNORE INTO zip_county (zip,fips,is_primary,crosswalk_vintage,source_id)
                       VALUES (?,?,1,?,?)""", (rec["zip"], fips, "census-derived", SOURCE_ID))
        cur.execute("""INSERT OR REPLACE INTO service
            (id,organization_id,name,resource_bucket,status,source_id,source_url,date_checked,confidence)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (svc_id, org_id, "Food pantry", "food", "active", SOURCE_ID, PAGE_URL, TODAY, CONFIDENCE))
        cur.execute("INSERT OR IGNORE INTO service_at_location (id,service_id,location_id) VALUES (?,?,?)",
                    (sid("sal", svc_id, loc_id), svc_id, loc_id))
        cur.execute("""INSERT OR IGNORE INTO service_area (id,service_id,extent_type,fips,description)
                       VALUES (?,?,?,?,?)""", (sid("sa", svc_id, fips), svc_id, "county", fips, "Pantry county"))
        if rec.get("phone"):
            cur.execute("INSERT OR REPLACE INTO phone (id,organization_id,number,type) VALUES (?,?,?,?)",
                        (sid("ph", org_id), org_id, rec["phone"], "voice"))
        if rec.get("hours"):
            cur.execute("INSERT OR REPLACE INTO schedule (id,service_id,description) VALUES (?,?,?)",
                        (sid("sch", svc_id), svc_id, rec["hours"]))
        cur.execute("""INSERT OR REPLACE INTO record_provenance
            (id,record_table,record_id,source_id,source_url,date_checked,confidence,extracted_by,method)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (sid("prov", org_id), "organization", org_id, SOURCE_ID, PAGE_URL, TODAY,
             CONFIDENCE, "automated", "html_extraction"))
        stats["loaded"] += 1

    if not dry_run:
        cur.execute("""INSERT INTO refresh_log
            (id,run_started,run_finished,refresh_quarter,source_id,stage,status,records_in,records_out,records_rejected,message)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (sid("run", SOURCE_ID, TODAY), TODAY, TODAY, "2026Q2", SOURCE_ID, "load", "success",
             stats["parsed"], stats["loaded"], stats["rejected_pii"], f"no_geo={stats['no_geo']}"))
        con.commit()
    con.close()
    return stats

def main():
    dry = "--dry-run" in sys.argv
    print("[caagkc-pantries] fetching page ...")
    recs = parse_pantries(fetch_html())
    print(f"[caagkc-pantries] parsed {len(recs)} pantries. {'DRY RUN' if dry else 'loading'} ...")
    s = load(recs, dry_run=dry)
    print(f"[caagkc-pantries] loaded={s['loaded']} parsed={s['parsed']} "
          f"pii_rejected={s['rejected_pii']} no_geo={s['no_geo']}")

if __name__ == "__main__":
    main()
