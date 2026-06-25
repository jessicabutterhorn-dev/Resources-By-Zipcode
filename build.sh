#!/usr/bin/env bash
# Rebuild the SQLite DB from schema + seed, then regenerate the front-end data.
# Quarterly production runs replace seed.sql with the real verified load.
set -euo pipefail
cd "$(dirname "$0")"
rm -f db/resources.db
sqlite3 db/resources.db < db/schema.sql
sqlite3 db/resources.db < db/seed.sql
python3 pipeline/build_frontend.py
python3 pipeline/gen_credits.py
echo "Done. Open frontend/index.html in any browser."
