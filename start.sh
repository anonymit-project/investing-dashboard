#!/bin/bash
# ── Stock Dashboard — Arranque Mac / Linux ─────────────────────────────────
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📈  Stock Dashboard — Value Investing  "
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Comprobar Python
if ! command -v python3 &>/dev/null; then
  echo "❌  Python 3 no encontrado. Instálalo desde https://python.org"
  exit 1
fi

PYTHON=python3
PIP=pip3

# Comprobar pip
if ! command -v pip3 &>/dev/null; then
  echo "⚠️  pip3 no encontrado. Intentando con python -m pip..."
  PIP="$PYTHON -m pip"
fi

# Instalar dependencias si faltan
echo "📦  Verificando dependencias..."
$PIP install --quiet flask flask-cors yfinance pandas gunicorn 2>&1 | grep -E "^(Collecting|Installing|Successfully|Requirement)" || true

echo ""
echo "🚀  Arrancando servidor Flask en http://localhost:5000 ..."
echo "    Pulsa Ctrl+C para detener."
echo ""

# Abrir navegador (Mac / Linux)
open_browser() {
  sleep 2
  if command -v open &>/dev/null; then
    open "http://localhost:5000"        # macOS
  elif command -v xdg-open &>/dev/null; then
    xdg-open "http://localhost:5000"    # Linux con entorno gráfico
  fi
}
open_browser &

# Lanzar Flask
FLASK_ENV=development $PYTHON app.py
