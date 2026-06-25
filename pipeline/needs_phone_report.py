#!/usr/bin/env python3
"""Generate docs/NEEDS_PHONE.md — orgs still missing a direct phone number.

These show the "Dial 211" fallback on the printout. This report gives the team
a worklist to find + verify (two sources) a direct number for each. Regenerated
every build, so it shrinks as numbers are added to data/phone_overrides.json.

Stdlib only.
"""
import os, sqlite3, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "resources.db")
OUT = os.path.join(ROOT, "docs", "NEEDS_PHONE.md")

def main():
    con = sqlite3.connect(DB)
    rows = con.execute("""
        SELECT o.name,
               group_concat(DISTINCT s.resource_bucket),
               COALESCE(o.website,''),
               src.source_name,
               COALESCE((SELECT a.city FROM service_at_location sal JOIN location l ON l.id=sal.location_id
                         JOIN address a ON a.location_id=l.id JOIN service sv ON sv.id=sal.service_id
                         WHERE sv.organization_id=o.id LIMIT 1),''),
               COALESCE((SELECT a.state_province FROM service_at_location sal JOIN location l ON l.id=sal.location_id
                         JOIN address a ON a.location_id=l.id JOIN service sv ON sv.id=sal.service_id
                         WHERE sv.organization_id=o.id LIMIT 1),'')
        FROM organization o
        JOIN source src ON src.id = o.source_id
        JOIN service s  ON s.organization_id = o.id
        LEFT JOIN phone p ON p.organization_id = o.id
        WHERE p.id IS NULL
        GROUP BY o.id
        ORDER BY 2, o.name""").fetchall()
    total = con.execute("SELECT count(*) FROM organization").fetchone()[0]
    con.close()

    today = datetime.date.today().isoformat()
    lines = [
        "# Needs Phone — team worklist",
        "",
        f"_Generated {today}. {len(rows)} of {total} provider orgs have no direct phone "
        f"({round(100.0*(total-len(rows))/total,1)}% have one). These show \"Dial 211\" on the "
        "printout until a number is added._",
        "",
        "**How to add one:** find the org's public phone, **verify it on a second independent "
        "source** (org site + a directory like 211/findhelp/GuideStar/Google Business), then add "
        "`\"<org_id>\": \"(xxx) xxx-xxxx\"` to `data/phone_overrides.json` and rebuild. (Ask the dev "
        "for the org_id, or drop the verified number here and it'll be wired in.)",
        "",
        "| Org | Category | City | Website | Verified phone (fill in) | 2nd source |",
        "|---|---|---|---|---|---|",
    ]
    for name, buckets, web, src, city, state in rows:
        loc = f"{city}, {state}".strip(", ")
        web_md = f"[link]({web})" if web else "—"
        lines.append(f"| {name} | {buckets} | {loc or '—'} | {web_md} |  |  |")
    lines.append("")
    with open(OUT, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"[needs-phone] wrote {OUT}: {len(rows)} orgs need a phone")

if __name__ == "__main__":
    main()
