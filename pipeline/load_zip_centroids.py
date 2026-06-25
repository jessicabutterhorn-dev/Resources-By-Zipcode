#!/usr/bin/env python3
"""Load ZIP-code centroids (lat/lon) so the front-end can sort results by
distance and show 'X miles away'.

Source: Census ZCTA Gazetteer (public domain). We keep only the ZIPs that are
searchable in this directory (present in zip_county). Writes a small JSON the
build reads — no DB change, no rebuild of the connectors.

Run before build_frontend (it is wired into build_real.sh / build.sh).
Stdlib only.
"""
import io, json, os, sqlite3, sys, urllib.request, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "db", "resources.db")
OUT = os.path.join(ROOT, "data", "zip_centroids.json")
UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"
GAZ = "https://www2.census.gov/geo/docs/maps-data/data/gazetteer/2023_Gazetteer/2023_Gaz_zcta_national.zip"

def main():
    con = sqlite3.connect(DB)
    want = {r[0] for r in con.execute("SELECT DISTINCT zip FROM zip_county")}
    con.close()
    if not want:
        sys.exit("no ZIPs in zip_county yet")

    req = urllib.request.Request(GAZ, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    zf = zipfile.ZipFile(io.BytesIO(raw))
    inner = [n for n in zf.namelist() if n.lower().endswith(".txt")][0]
    text = zf.read(inner).decode("latin-1")

    out = {}
    lines = text.splitlines()
    header = lines[0].split("\t")
    hi = {h.strip(): i for i, h in enumerate(header)}
    gi, lat_i, lon_i = hi["GEOID"], hi["INTPTLAT"], hi["INTPTLONG"]
    for line in lines[1:]:
        c = line.split("\t")
        if len(c) <= lon_i:
            continue
        z = c[gi].strip()
        if z in want:
            try:
                out[z] = [round(float(c[lat_i]), 6), round(float(c[lon_i]), 6)]
            except ValueError:
                pass
    json.dump(out, open(OUT, "w"))
    print(f"[zip-centroids] {len(out)}/{len(want)} searchable ZIPs matched -> {OUT}")
    missing = sorted(want - set(out))
    if missing:
        sys.stderr.write(f"[zip-centroids] {len(missing)} ZIPs without a centroid (no distance shown): {missing[:10]}\n")

if __name__ == "__main__":
    main()
