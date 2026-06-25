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
python3 pipeline/build_frontend.py
echo "Done. Open frontend/index.html — real open-data records."
