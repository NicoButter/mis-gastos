#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
exec .venv/bin/python backend/manage.py runserver 127.0.0.1:8000
