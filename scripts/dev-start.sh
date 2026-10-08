#!/usr/bin/env bash
# Inicia el entorno de desarrollo local de Gastio (Django + Angular).
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
backend_pid=""
frontend_pid=""

info() {
  printf '\n[ Gastio ] %s\n' "$1"
}

fail() {
  printf '\n[ Gastio ] ERROR: %s\n' "$1" >&2
  exit 1
}

stop_process() {
  local pid="$1"
  local name="$2"

  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    info "Deteniendo $name (PID $pid)..."
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
}

cleanup() {
  local status="$1"
  trap - EXIT INT TERM
  info "Finalizando el entorno de desarrollo..."
  stop_process "$frontend_pid" "frontend"
  stop_process "$backend_pid" "backend"
  exit "$status"
}

usage() {
  cat <<'EOF'
Uso: ./scripts/dev-start.sh

Carga .env, verifica las dependencias locales y la conexión PostgreSQL, aplica
las migraciones pendientes y levanta Django y Angular. Presioná Ctrl+C para
detener ambos procesos.
EOF
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

cd "$project_dir"
info "Preparando el entorno local en $project_dir"

[[ -f .env ]] || fail "No existe .env. Crealo con: cp .env.example .env"
[[ -x .venv/bin/python ]] || fail "No existe el entorno Python. Ejecutá: ./scripts/setup.sh"
[[ -d frontend/node_modules ]] || fail "Faltan dependencias del frontend. Ejecutá: ./scripts/setup.sh"
command -v npm >/dev/null 2>&1 || fail "No se encontró npm en PATH."

info "Cargando las variables de entorno desde .env"
set -a
source .env
set +a
[[ -n "${DATABASE_URL:-}" ]] || fail "DATABASE_URL no está definida en .env."

info "Verificando configuración de Django y conexión con PostgreSQL..."
.venv/bin/python backend/manage.py check
.venv/bin/python backend/manage.py shell -c "from django.db import connection; connection.cursor().execute('SELECT 1'); print('Conexión PostgreSQL verificada.')"

info "Aplicando migraciones pendientes en la base configurada..."
.venv/bin/python backend/manage.py migrate --noinput

info "Levantando backend Django en http://localhost:8000"
./scripts/run-backend.sh > >(sed -u 's/^/[backend] /') 2>&1 &
backend_pid=$!

info "Levantando frontend Angular en http://localhost:4200"
npm --prefix frontend start -- --host localhost > >(sed -u 's/^/[frontend] /') 2>&1 &
frontend_pid=$!

trap 'cleanup $?' EXIT
trap 'exit 130' INT TERM

info "Servicios iniciados. Abrí http://localhost:4200/"
info "API de salud: http://localhost:8000/api/v1/health/"
info "Los logs se identifican con [backend] y [frontend]. Presioná Ctrl+C para detenerlos."
info "Redis y Celery no se levantan: son opcionales y no se requieren en la Fase 0."

# Si uno de los servidores termina, se detiene el otro y se devuelve su estado.
wait -n "$backend_pid" "$frontend_pid"
