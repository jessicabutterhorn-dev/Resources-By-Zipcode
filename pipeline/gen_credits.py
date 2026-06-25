#!/usr/bin/env python3
"""Generate frontend/credits.html — sources, licenses, attribution.

Reads the `source` table (every record's provenance points here) and renders a
standalone, printable credits page. Required before publishing: CC-BY / open
sources need visible attribution, and it documents the no-PHI posture.

Run as part of the build (build.sh / build_real.sh). Stdlib only.
"""
import os, sqlite3, html, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "resources.db")
OUT = os.path.join(ROOT, "frontend", "credits.html")

LANE_LABEL = {"open": "Open / public-domain", "licensed": "Licensed",
              "agreement_required": "Agreement-gated"}

def esc(s):
    return html.escape(str(s)) if s is not None else ""

def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    # per-source record count (organizations carrying that source_id)
    counts = dict(cur.execute("SELECT source_id, count(*) FROM organization GROUP BY source_id").fetchall())
    cols = "id,source_name,publisher,source_url,license,attribution_text,attribution_required,access_route,date_checked,refresh_mode,confidence,notes"
    srcs = [dict(zip(cols.split(","), r))
            for r in cur.execute(f"SELECT {cols} FROM source ORDER BY source_name").fetchall()]
    con.close()

    today = datetime.date.today().isoformat()
    rows = ""
    for s in srcs:
        n = counts.get(s["id"], 0)
        attro = "Yes" if s["attribution_required"] else "—"
        link = s["source_url"] or ""
        rows += (
            "<tr>"
            f"<td><strong>{esc(s['source_name'])}</strong>"
            + (f"<div class='pub'>{esc(s['publisher'])}</div>" if s['publisher'] else "")
            + (f"<div class='attr'>{esc(s['attribution_text'])}</div>" if s['attribution_text'] else "")
            + "</td>"
            f"<td>{esc(s['license'])}<div class='lane'>{esc(LANE_LABEL.get(s['access_route'], s['access_route']))}</div></td>"
            f"<td class='num'>{n}</td>"
            f"<td>{esc(s['attribution_required'] and 'Yes' or '—')}</td>"
            f"<td>{esc(s['date_checked'])}</td>"
            f"<td><a href='{esc(link)}' target='_blank' rel='noopener'>link</a></td>"
            "</tr>\n"
        )

    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sources &amp; Credits — KS + MO Community Resource Finder</title>
<style>
  body {{ margin:0; font:16px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; color:#1a2230; background:#f4f6fa; }}
  .wrap {{ max-width:900px; margin:0 auto; padding:24px 18px 60px; }}
  h1 {{ font-size:24px; margin:14px 0 4px; }}
  p.lead {{ color:#5a6678; margin:0 0 18px; }}
  a.back {{ font-size:14px; }}
  table {{ width:100%; border-collapse:collapse; background:#fff; border:1px solid #d8dee8; border-radius:10px; overflow:hidden; }}
  th, td {{ text-align:left; padding:10px 12px; border-bottom:1px solid #eef1f6; vertical-align:top; font-size:14px; }}
  th {{ background:#eef4fb; font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:#5a6678; }}
  td.num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .pub {{ color:#5a6678; font-size:13px; }}
  .attr {{ color:#34414f; font-size:12px; margin-top:4px; font-style:italic; }}
  .lane {{ color:#5a6678; font-size:12px; }}
  .box {{ background:#fff; border:1px solid #d8dee8; border-radius:10px; padding:16px; margin:18px 0; font-size:14px; }}
  .box h2 {{ font-size:16px; margin:0 0 8px; }}
  footer {{ color:#5a6678; font-size:12px; margin-top:24px; }}
  @media print {{ body {{ background:#fff; }} a.back {{ display:none; }} }}
</style>
</head>
<body>
<div class="wrap">
  <a class="back" href="index.html">&larr; Back to the resource finder</a>
  <h1>Sources &amp; Credits</h1>
  <p class="lead">This directory compiles <strong>public</strong> information about community-service
  providers across Kansas and Missouri. It contains no personal or health information about any member.</p>

  <div class="box">
    <h2>How to read the listings</h2>
    Every listing shows the <strong>source</strong> it came from, the <strong>date it was last checked</strong>,
    and a <strong>confidence</strong> badge. Records marked <em>unverified</em> are starting points that have not
    yet been confirmed — always call ahead before relying on any listing, as hours and programs change.
  </div>

  <table>
    <thead><tr><th>Source</th><th>License</th><th>Records</th><th>Attribution req.</th><th>Last checked</th><th></th></tr></thead>
    <tbody>
{rows}    </tbody>
  </table>

  <div class="box">
    <h2>Privacy &amp; HIPAA</h2>
    This is a directory of public organizations — comparable to a phone book. It stores no member names,
    Medicare IDs, dates of birth, claims, or health information, so it is out of scope for HIPAA by design.
  </div>

  <footer>Generated {today}. Data sourced under each provider's license; attribution shown where required.</footer>
</div>
</body>
</html>
"""
    with open(OUT, "w") as f:
        f.write(doc)
    print(f"[credits] wrote {OUT}: {len(srcs)} sources, {sum(counts.values())} attributed records")

if __name__ == "__main__":
    main()
