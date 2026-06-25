#!/usr/bin/env python3
"""Build the static front-end data file from the SQLite source of truth.

Reads db/resources.db, writes frontend/data.js (an embedded JSON blob the page
reads with plain JS — no server, no internet, double-click to open).

This is the `build_frontend` stage of the quarterly pipeline. Re-run after every
DB rebuild. For the demo it exports the [SAMPLE] seed data.

Usage:  python3 pipeline/build_frontend.py
"""
import json, os, sqlite3, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "resources.db")
OUT = os.path.join(ROOT, "frontend", "data.js")
REFERRALS = os.path.join(ROOT, "data", "referrals.json")

BUCKET_LABELS = {
    "food": "Food & Groceries", "utility": "Utility Assistance",
    "rent": "Rent Assistance", "pet_food": "Pet Food",
    "hygiene": "Hygiene & Personal Care",
    "gas_transport": "Gas & Transportation", "prescription": "Prescription Help",
    "housing": "Housing", "navigation": "Help Finding Services",
}

def rows(cur, sql, args=()):
    cur.execute(sql, args)
    cols = [c[0] for c in cur.description]
    return [dict(zip(cols, r)) for r in cur.fetchall()]

def build():
    con = sqlite3.connect(DB)
    con.execute("PRAGMA foreign_keys = ON")
    cur = con.cursor()

    zips = rows(cur, "SELECT DISTINCT zip FROM zip_county ORDER BY zip")
    data = {}
    for z in zips:
        zip_code = z["zip"]
        geo = rows(cur, """SELECT county_name, state, zone_id, zone_name
                           FROM v_zip_zone WHERE zip=? AND is_primary=1 LIMIT 1""", (zip_code,))
        geo = geo[0] if geo else {}

        # all county FIPS this ZIP touches (a ZIP may span counties, e.g. Kansas City)
        fips_list = [r["fips"] for r in rows(cur, "SELECT fips FROM zip_county WHERE zip=?", (zip_code,))]
        ph_in = ",".join("?" * len(fips_list))

        # A service is shown for this ZIP if it COVERS the ZIP's county, either by
        # an explicit service_area (regional, e.g. a CAA serving many counties) OR
        # by having an office located in that county.
        res = rows(cur, f"""
            SELECT DISTINCT s.id svc_id, s.name service_name, s.resource_bucket,
                   s.description, s.application_process, s.fees,
                   o.name org_name, o.website,
                   s.confidence, s.source_url, s.date_checked
            FROM service s
            JOIN organization o ON o.id = s.organization_id
            WHERE s.status='active' AND (
                s.id IN (SELECT service_id FROM service_area WHERE fips IN ({ph_in}))
                OR s.id IN (
                    SELECT sal.service_id FROM service_at_location sal
                    JOIN location l ON l.id = sal.location_id
                    JOIN address a  ON a.location_id = l.id
                    WHERE a.fips IN ({ph_in})
                )
            )
            ORDER BY s.resource_bucket, o.name""", fips_list + fips_list)

        for r in res:
            # display address: prefer an office in the searched county, else any office
            addr = rows(cur, f"""SELECT a.address_1, a.city, a.state_province, a.postal_code
                FROM service_at_location sal
                JOIN location l ON l.id = sal.location_id
                JOIN address a  ON a.location_id = l.id
                WHERE sal.service_id=?
                ORDER BY (a.fips IN ({ph_in})) DESC LIMIT 1""", [r["svc_id"]] + fips_list)
            a = addr[0] if addr else {}
            r["address_1"] = a.get("address_1"); r["city"] = a.get("city")
            r["state_province"] = a.get("state_province"); r["postal_code"] = a.get("postal_code")
            ph = rows(cur, """SELECT number FROM phone
                              WHERE organization_id=(SELECT organization_id FROM service WHERE id=?)
                              ORDER BY id LIMIT 1""", (r["svc_id"],))
            r["phone"] = ph[0]["number"] if ph else None
            sch = rows(cur, "SELECT description FROM schedule WHERE service_id=? LIMIT 1", (r["svc_id"],))
            r["hours"] = sch[0]["description"] if sch else None
            el = rows(cur, "SELECT description FROM eligibility WHERE service_id=? LIMIT 1", (r["svc_id"],))
            r["eligibility"] = el[0]["description"] if el else None
            r["bucket_label"] = BUCKET_LABELS.get(r["resource_bucket"], r["resource_bucket"])
            del r["svc_id"]

        # The directory tracks ONLY available community resources.

        data[zip_code] = {
            "county": geo.get("county_name"), "state": geo.get("state"),
            "zone_id": geo.get("zone_id"), "zone_name": geo.get("zone_name"),
            "resources": res,
        }

    # sample flag = any [SAMPLE] org present -> page shows the SAMPLE banner
    cur.execute("SELECT count(*) FROM organization WHERE name LIKE '[SAMPLE]%'")
    is_sample = cur.fetchone()[0] > 0
    con.close()
    referrals = []
    if os.path.exists(REFERRALS):
        referrals = json.load(open(REFERRALS)).get("referrals", [])
    payload = {
        "generated": "STATIC EXPORT",   # date stamped by pipeline run, omitted in demo
        "sample": is_sample,            # true only when sample rows are present
        "bucket_labels": BUCKET_LABELS,
        "referrals": referrals,         # statewide/national link-outs, state-aware
        "zips": data,
    }
    with open(OUT, "w") as f:
        f.write("// AUTO-GENERATED by pipeline/build_frontend.py — do not edit by hand.\n")
        f.write("window.RESOURCE_DATA = ")
        json.dump(payload, f, indent=1)
        f.write(";\n")
    print(f"wrote {OUT}: {len(data)} ZIPs")

if __name__ == "__main__":
    build()
