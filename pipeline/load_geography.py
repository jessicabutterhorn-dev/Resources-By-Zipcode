#!/usr/bin/env python3
"""Load the KS+MO geography spine: zone, county, county_zone.

Sources (both public domain / open):
  * data/zones.json            — canonical 6-zone -> county-name map.
  * Census national county file — county name <-> FIPS for KS (20) + MO (29).

Populates `county` (all 105 KS + 115 MO), `zone` (1..6 from zones.json), and
`county_zone` (every county assigned to exactly one zone). Idempotent.

Run before the connectors so name->FIPS resolution + zone assignment work.

Stdlib only.
"""
import json, os, re, sqlite3, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "resources.db")
ZONES_JSON = os.path.join(ROOT, "data", "zones.json")
CENSUS_COUNTY = "https://www2.census.gov/geo/docs/reference/codes2020/national_county2020.txt"
UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"

def norm(name):
    """Normalize a county name for matching: lowercase, drop punctuation + ' county' suffix."""
    return re.sub(r"[^a-z ]", "", name.lower()).replace(" county", "").strip()

def fetch_census_counties(states_set):
    req = urllib.request.Request(CENSUS_COUNTY, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        text = r.read().decode("utf-8")
    out = []
    for line in text.splitlines():
        parts = line.split("|")
        if len(parts) < 6 or parts[0] not in states_set:
            continue
        state, statefp, countyfp, _ns, cname, classfp = parts[:6]
        fips = statefp + countyfp
        # bare name, no "County" suffix; keep "city" for independent cities
        bare = re.sub(r"\s+County$", "", cname).strip()
        out.append({"fips": fips, "name": bare, "state": state,
                    "indep_city": 1 if classfp.startswith("C") else 0})
    return out

def load_zone_resolver(zones):
    resolver = {}
    for zone in zones["zones"]:
        for st, counties in zone["counties"].items():
            for cty in counties:
                resolver[(st, norm(cty))] = zone["zone_id"]
    return resolver

def main():
    states_set = set(sys.argv[sys.argv.index("--states") + 1].upper().split(",")) if "--states" in sys.argv else {"KS", "MO"}
    zones = json.load(open(ZONES_JSON))
    resolver = load_zone_resolver(zones)
    counties = fetch_census_counties(states_set)

    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    # zones
    for z in zones["zones"]:
        cur.execute("""INSERT OR REPLACE INTO zone (zone_id, zone_name, approx_population, major_metros)
                       VALUES (?,?,?,?)""",
                    (z["zone_id"], z["zone_name"], z.get("approx_population"),
                     json.dumps(z.get("major_metros", []))))

    loaded, unmatched = 0, []
    for c in counties:
        cur.execute("""INSERT OR REPLACE INTO county (fips, county_name, state, is_independent_city)
                       VALUES (?,?,?,?)""",
                    (c["fips"], c["name"], c["state"], c["indep_city"]))
        zone_id = resolver.get((c["state"], norm(c["name"])))
        if zone_id is None:
            unmatched.append(f"{c['name']}, {c['state']} ({c['fips']})")
            continue
        cur.execute("INSERT OR REPLACE INTO county_zone (fips, zone_id) VALUES (?,?)",
                    (c["fips"], zone_id))
        loaded += 1

    con.commit()
    nz = cur.execute("SELECT count(*) FROM county").fetchone()[0]
    ncz = cur.execute("SELECT count(*) FROM county_zone").fetchone()[0]
    con.close()
    print(f"[geography] counties={nz} county_zone={ncz} zones={len(zones['zones'])}")
    if unmatched:
        sys.stderr.write(f"[geography] WARNING {len(unmatched)} counties not matched to a zone:\n")
        for u in unmatched:
            sys.stderr.write(f"    {u}\n")

if __name__ == "__main__":
    main()
