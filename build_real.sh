#!/usr/bin/env bash
# Build the DB from REAL open-route data (no [SAMPLE] seed), then the front-end.
# Proves the live pipeline path: schema -> connector(s) -> front-end.
# Add more open-route connectors below as they are built.
set -euo pipefail
cd "$(dirname "$0")"
rm -f db/resources.db
sqlite3 db/resources.db < db/schema.sql
python3 pipeline/connectors/data_mo_gov.py
python3 pipeline/build_frontend.py
echo "Done. Open frontend/index.html — real data.mo.gov records."
