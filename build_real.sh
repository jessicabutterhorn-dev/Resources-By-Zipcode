#!/usr/bin/env bash
# Build the DB from REAL open-route data (no [SAMPLE] seed), then the front-end.
# Proves the live pipeline path: schema -> geography -> connectors -> front-end.
# Add more open-route connectors to the list below as they are built.
set -euo pipefail
cd "$(dirname "$0")"
rm -f db/resources.db
sqlite3 db/resources.db < db/schema.sql
python3 pipeline/load_geography.py
python3 pipeline/connectors/data_mo_gov.py        # MO Job Centers (navigation)
python3 pipeline/connectors/liheap_mo_caa.py      # MO LIHEAP / energy (utility, food, housing)
python3 pipeline/connectors/hud_housing_counseling.py  # HUD housing counseling (KS + MO housing)
python3 pipeline/connectors/caagkc_pantries.py    # CAAGKC partner food pantries (KC metro, food)
python3 pipeline/connectors/ofs_metro.py          # Operation Food Search (St. Louis metro, food)
python3 pipeline/connectors/hygiene_stl.py        # Curated St. Louis hygiene kits (UNVERIFIED)
python3 pipeline/connectors/aaa_seniors.py        # KS+MO Area Agencies on Aging (senior food/transport/navigation)
python3 pipeline/connectors/free_resource.py --bucket dental --records data/dental_records.json --source-id free-dental --source-name "Free non-profit dental (KS+MO)" --service-name "Free dental care" --dir-url https://dentallifeline.org/
python3 pipeline/connectors/free_resource.py --bucket vision --records data/vision_records.json --source-id free-vision --source-name "Free non-profit vision (KS+MO)" --service-name "Free vision care / eyeglasses" --dir-url https://lionsclubs.org/
python3 pipeline/connectors/free_resource.py --bucket prescription --records data/rx_records.json --source-id rx-assist --source-name "Free/charitable prescription assistance (KS+MO)" --service-name "Prescription assistance" --dir-url https://www.needymeds.org/
python3 pipeline/connectors/free_resource.py --bucket rent --records data/rent_records.json --source-id rent-assist --source-name "Nonprofit & govt rent assistance (KS+MO)" --service-name "Emergency rent assistance" --dir-url https://www.211.org/
python3 pipeline/connectors/free_resource.py --bucket pet_food --records data/petfood_records.json --source-id petfood-assist --source-name "Free pet-food assistance (KS+MO)" --service-name "Pet food assistance" --dir-url https://www.feedingamerica.org/
python3 pipeline/load_zip_centroids.py
python3 pipeline/build_frontend.py
python3 pipeline/gen_credits.py
echo "Done. Open frontend/index.html — real open-data records."
