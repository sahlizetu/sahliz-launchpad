#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Configurez la connexion de la base dans Render.}"

python -m pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput

if [[ -n "${DEMO_WALLETS:-}" ]]; then
    read -r -a wallets <<< "$DEMO_WALLETS"
    python manage.py seed_startups "${wallets[@]}"
fi
