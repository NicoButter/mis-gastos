#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

if [[ -f .env ]]; then
  set -a
  source .env
  set +a
fi
exec .venv/bin/celery -A config.celery worker --workdir backend --loglevel=INFO
