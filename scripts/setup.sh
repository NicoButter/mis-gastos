#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_dir"

python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r backend/requirements/dev.txt
npm --prefix frontend ci

if [[ ! -f .env ]]; then
  cp .env.example .env
  printf 'Se creó .env; revisá sus valores antes de iniciar.\n'
fi
