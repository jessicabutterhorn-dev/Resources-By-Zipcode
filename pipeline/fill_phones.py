#!/usr/bin/env python3
"""Fill missing org phone numbers from data/phone_overrides.json.

Every resource on a printout must have a phone (clients may have no computer).
Connectors load what their source provides; this step backfills phones found by
the find-phones workflow, keyed by the org's STABLE id (deterministic hash, so
the mapping survives rebuilds). Runs after all connectors, before build_frontend.

Stdlib only.
"""
import json, os, sqlite3, hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "resources.db")
OVERRIDES = os.path.join(ROOT, "data", "phone_overrides.json")

def sid(*p): return hashlib.sha1("|".join(str(x) for x in p).encode()).hexdigest()[:24]

def main():
    if not os.path.exists(OVERRIDES):
        print("[fill-phones] no overrides file; skipping"); return
    ov = json.load(open(OVERRIDES))
    con = sqlite3.connect(DB); con.execute("PRAGMA foreign_keys=ON"); cur = con.cursor()
    have = {r[0] for r in cur.execute("SELECT DISTINCT organization_id FROM phone WHERE organization_id IS NOT NULL")}
    orgs = {r[0] for r in cur.execute("SELECT id FROM organization")}
    filled = skipped = 0
    for org_id, phone in ov.items():
        if not phone or org_id not in orgs or org_id in have:
            skipped += 1; continue
        cur.execute("INSERT OR REPLACE INTO phone (id,organization_id,number,type) VALUES (?,?,?,?)",
                    (sid("ph-fill", org_id), org_id, phone, "voice"))
        filled += 1
    con.commit()
    remaining = cur.execute("""SELECT count(*) FROM organization o
        LEFT JOIN phone p ON p.organization_id=o.id WHERE p.id IS NULL""").fetchone()[0]
    con.close()
    print(f"[fill-phones] filled={filled} skipped={skipped} orgs_still_without_phone={remaining}")

if __name__ == "__main__":
    main()
