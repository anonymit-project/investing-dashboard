"""
app.py — Servidor Flask para el Stock Dashboard de Value Investing.
"""

import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from data import TICKERS, get_all_stocks, get_stock_detail, invalidate_cache

app = Flask(__name__, static_folder=".")
CORS(app, resources={r"/*": {"origins": "*"}})

# ── Ruta raíz: sirve el dashboard ─────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory(".", "dashboard.html")

# ── GET /api/stocks ───────────────────────────────────────────────────────────
@app.route("/api/stocks")
def api_stocks():
    """
    Acepta ?tickers=AAPL,MSFT,...
    Si no se pasan, usa el universo por defecto (TICKERS).
    """
    tickers_param = request.args.get("tickers", "")
    if tickers_param:
        tickers = [t.strip().upper() for t in tickers_param.split(",") if t.strip()]
    else:
        tickers = TICKERS

    data = get_all_stocks(tickers)
    return jsonify(data)

# ── GET /api/stock/<ticker> ───────────────────────────────────────────────────
@app.route("/api/stock/<ticker>")
def api_stock_detail(ticker: str):
    """Devuelve detalle completo: métricas, historial de precio, desglose del score."""
    data = get_stock_detail(ticker.upper())
    return jsonify(data)

# ── GET /api/refresh ──────────────────────────────────────────────────────────
@app.route("/api/refresh")
def api_refresh():
    """Invalida la caché en memoria y devuelve confirmación."""
    invalidate_cache()
    return jsonify({"status": "ok", "message": "Caché invalidada. Los datos se recargarán en la próxima solicitud."})

# ── GET /api/tickers ──────────────────────────────────────────────────────────
@app.route("/api/tickers")
def api_tickers():
    """Devuelve la lista de tickers por defecto."""
    return jsonify({"tickers": TICKERS})

# ── Arranque ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "production") == "development"
    print(f"🚀 Stock Dashboard arrancando en http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
