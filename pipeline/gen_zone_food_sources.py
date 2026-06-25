#!/usr/bin/env python3
"""Generate data/zone_food_sources.json — the safe-route food-source map per zone.

Maps each of the 6 collection zones to its anchor Feeding America food bank(s)
(whose public agency/pantry locators yield ALL pantries in that zone) plus the
collection notes a per-zone agent/connector would use. Verifies each anchor URL
is live (HEAD/GET) so entries are grounded, not guessed.

This is the structured target for the 6-zone food-pantry search: instead of
scraping 220 counties blind, each zone has a named food bank + locator to pull
from (safe-route: food banks publish partner-agency directories publicly).
"""
import json, os, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "zone_food_sources.json")
UA = "ks-mo-resource-directory/0.1 (public-data ingest; non-commercial)"

# Feeding America member food banks serving KS+MO, mapped to our zones.
ZONES = {
  1: {"zone_name": "Kansas City Metro (Bi-State Core)",
      "anchor_food_banks": [
        {"name": "Harvesters – The Community Food Network", "url": "https://www.harvesters.org/",
         "locator": "https://www.harvesters.org/GetHelp", "coverage": "NW Missouri + NE Kansas (incl. KC metro both sides)"}],
      "named_pantry_source": "CAAGKC partner pantries (already ingested via caagkc_pantries.py)",
      "support_orgs": ["Community Action Agency of Greater KC (CAAGKC)", "United Way of Greater KC 211"]},
  2: {"zone_name": "St. Louis Metro + Eastern Missouri",
      "anchor_food_banks": [
        {"name": "St. Louis Area Foodbank", "url": "https://stlfoodbank.org/",
         "locator": "https://stlfoodbank.org/get-help/", "coverage": "26 counties E. Missouri + S. Illinois"}],
      "support_orgs": ["United Way of Greater St. Louis 211", "Urban League of Metro St. Louis"]},
  3: {"zone_name": "Central + Northeast Missouri",
      "anchor_food_banks": [
        {"name": "The Food Bank for Central & Northeast Missouri", "url": "https://sharefoodbringhope.org/",
         "locator": "https://sharefoodbringhope.org/find-food/", "coverage": "32 counties central/NE Missouri"}],
      "support_orgs": ["Central Missouri Community Action (CMCA)", "Heart of Missouri United Way 211"]},
  4: {"zone_name": "Southwest + South-Central Missouri (Ozarks + Bootheel)",
      "anchor_food_banks": [
        {"name": "Ozarks Food Harvest", "url": "https://ozarksfoodharvest.org/",
         "locator": "https://ozarksfoodharvest.org/get-help/", "coverage": "28 counties SW Missouri (Ozarks)"}],
      "support_orgs": ["Ozarks Area Community Action Corp (OACAC)", "Catholic Charities of Southern Missouri"]},
  5: {"zone_name": "Northwest Missouri + Eastern/North-Central Kansas",
      "anchor_food_banks": [
        {"name": "Second Harvest Community Food Bank", "url": "https://www.shcfb.org/",
         "locator": "https://www.shcfb.org/find-food/", "coverage": "NW Missouri + NE Kansas (St. Joseph hub)"},
        {"name": "Harvesters – The Community Food Network", "url": "https://www.harvesters.org/",
         "locator": "https://www.harvesters.org/GetHelp", "coverage": "NE/N-central Kansas (Topeka area)"}],
      "support_orgs": ["Kansas DCF (LIEAP/food)", "Community Action partners (NW MO)"]},
  6: {"zone_name": "Central + Western Kansas",
      "anchor_food_banks": [
        {"name": "Kansas Food Bank", "url": "https://www.kansasfoodbank.org/",
         "locator": "https://www.kansasfoodbank.org/get-help/", "coverage": "85 counties central/western Kansas (Wichita hub)"}],
      "support_orgs": ["Kansas DCF", "Kansas Area Agencies on Aging (senior nutrition sites)"]},
}

def check(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except Exception as e:
        return "ERR:" + str(e)[:40]

def main():
    for zid, z in ZONES.items():
        for fb in z["anchor_food_banks"]:
            fb["url_status"] = check(fb["url"])
    payload = {
        "purpose": "Per-zone safe-route food-pantry + support-org collection targets for the 6-area search.",
        "method": "Each zone's anchor Feeding America food bank publishes a public partner-agency/pantry locator. Build one connector per food bank (robots-checked, attribution) to ingest all pantries in that zone. Prefer official food-bank directories + .gov + 211 (where licensed) over arbitrary scraping.",
        "national_locator": "https://www.feedingamerica.org/find-your-local-foodbank",
        "hsds_feed_note": "Feeding America HSDS feed (feedam.org/hsds) is the structured option — confirm attribution/terms before bulk load (sources.yaml: feeding-america-hsds, currently gated).",
        "zones": ZONES,
    }
    with open(OUT, "w") as f:
        json.dump(payload, f, indent=1)
    print("wrote", OUT)
    for zid, z in ZONES.items():
        fbs = "; ".join(f"{fb['name']} [{fb['url_status']}]" for fb in z["anchor_food_banks"])
        print(f"  Zone {zid}: {fbs}")

if __name__ == "__main__":
    main()
