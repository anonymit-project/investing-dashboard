"""
data.py — Lógica de obtención de datos bursátiles y cálculo de score de valor.
Usa yfinance + pandas. Caché en memoria con TTL de 4 horas.
"""

import time
import math
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

# ── Universo de acciones ──────────────────────────────────────────────────────
TICKERS = [
    # S&P 500 / NASDAQ
    "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA",
    "JPM", "JNJ", "BRK-B", "V", "PG", "KO", "XOM", "WMT",
    "NVO", "TM",
    # Europa
    "ASML", "NESN.SW", "MC.PA", "SAP.DE", "OR.PA", "AIR.PA",
    "SIE.DE", "TTE.PA", "ULVR.L", "UNA.AS", "RACE.MI",
    # Hong Kong
    "0700.HK",
    # IBEX 35
    "ITX.MC", "SAN.MC", "BBVA.MC", "IBE.MC", "TEF.MC",
    "REP.MC", "ACS.MC", "ENG.MC", "FER.MC", "ACX.MC", "CLNX.MC",
]

# Mapeo ticker → mercado
_MARKET_MAP = {
    ".MC": "ES",
    ".PA": "EU",
    ".DE": "EU",
    ".SW": "EU",
    ".L":  "EU",
    ".AS": "EU",
    ".MI": "EU",
    ".HK": "HK",
}

def _market_for(ticker: str) -> str:
    for suffix, market in _MARKET_MAP.items():
        if ticker.endswith(suffix):
            return market
    return "US"

# ── Caché en memoria ──────────────────────────────────────────────────────────
_CACHE: dict = {}          # ticker → {data: dict, ts: float}
_CACHE_TTL = 4 * 3600      # 4 horas en segundos

def _cache_get(ticker: str):
    entry = _CACHE.get(ticker)
    if entry and (time.time() - entry["ts"]) < _CACHE_TTL:
        return entry["data"]
    return None

def _cache_set(ticker: str, data: dict):
    _CACHE[ticker] = {"data": data, "ts": time.time()}

def invalidate_cache():
    """Vacía la caché para forzar recarga."""
    _CACHE.clear()

# ── Cálculo de RSI-14 ─────────────────────────────────────────────────────────
def _calc_rsi(closes: pd.Series, period: int = 14) -> float:
    if len(closes) < period + 1:
        return None
    delta = closes.diff().dropna()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=period).mean().iloc[-1]
    avg_loss = loss.rolling(window=period).mean().iloc[-1]
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

# ── Scoring por métrica ───────────────────────────────────────────────────────
def _score_per(v):
    if v is None or math.isnan(v) or v <= 0:
        return None
    if v < 15:   return 100
    if v <= 25:  return 60
    return 20

def _score_pb(v):
    if v is None or math.isnan(v) or v <= 0:
        return None
    if v < 1.5:  return 100
    if v <= 3:   return 60
    return 20

def _score_peg(v):
    if v is None or math.isnan(v) or v <= 0:
        return None
    if v < 1:    return 100
    if v <= 2:   return 50
    return 10

def _score_ev_ebitda(v):
    if v is None or math.isnan(v) or v <= 0:
        return None
    if v < 8:    return 100
    if v <= 15:  return 55
    return 15

def _score_debt_equity(v):
    if v is None or math.isnan(v):
        return None
    if v < 50:   return 100
    if v <= 150: return 50
    return 10

def _score_roe(v):
    if v is None or math.isnan(v):
        return None
    pct = v * 100
    if pct > 20:  return 100
    if pct >= 10: return 60
    return 20

def _score_operating_margin(v):
    if v is None or math.isnan(v):
        return None
    pct = v * 100
    if pct > 20:  return 100
    if pct >= 10: return 55
    return 20

def _score_rsi(v):
    if v is None:
        return None
    if 20 <= v <= 35: return 100
    if 35 < v <= 50:  return 75
    if 50 < v <= 65:  return 50
    if 65 < v <= 75:  return 25
    if v > 75:        return 0
    # < 20 extremadamente sobrevendido → también buena oportunidad
    return 100

# Pesos base
_WEIGHTS = {
    "PER":              0.20,
    "P/B":              0.10,
    "PEG":              0.15,
    "EV/EBITDA":        0.15,
    "Deuda/Equity":     0.10,
    "ROE":              0.10,
    "Margen Operativo": 0.10,
    "RSI-14":           0.10,
}

def _calc_score(metrics: dict) -> tuple[float, dict]:
    """
    Devuelve (score_total 0-100, desglose por métrica).
    Si una métrica no está disponible, su peso se redistribuye entre las demás.
    """
    raw = {
        "PER":              _score_per(metrics.get("per")),
        "P/B":              _score_pb(metrics.get("pb")),
        "PEG":              _score_peg(metrics.get("peg")),
        "EV/EBITDA":        _score_ev_ebitda(metrics.get("ev_ebitda")),
        "Deuda/Equity":     _score_debt_equity(metrics.get("debt_equity")),
        "ROE":              _score_roe(metrics.get("roe")),
        "Margen Operativo": _score_operating_margin(metrics.get("operating_margin")),
        "RSI-14":           _score_rsi(metrics.get("rsi")),
    }

    available = {k: v for k, v in raw.items() if v is not None}
    if not available:
        return 0.0, raw

    total_weight = sum(_WEIGHTS[k] for k in available)
    breakdown = {}
    score = 0.0
    for k, pts in available.items():
        adjusted_w = _WEIGHTS[k] / total_weight  # peso normalizado
        contribution = pts * adjusted_w
        score += contribution
        breakdown[k] = {
            "raw_score":    pts,
            "weight":       round(_WEIGHTS[k] * 100, 1),
            "contribution": round(contribution, 2),
        }

    for k, v in raw.items():
        if v is None:
            breakdown[k] = {"raw_score": None, "weight": round(_WEIGHTS[k] * 100, 1), "contribution": 0}

    return round(score, 2), breakdown

def _signal(score: float) -> str:
    if score >= 65:  return "COMPRAR"
    if score >= 35:  return "NEUTRAL"
    return "VENDER"

def _safe(v):
    """Convierte NaN / Inf a None para serialización JSON."""
    if v is None:
        return None
    try:
        if math.isnan(v) or math.isinf(v):
            return None
    except TypeError:
        pass
    return v

# ── Función principal de obtención de datos ───────────────────────────────────
def _fetch_stock(ticker: str) -> dict:
    cached = _cache_get(ticker)
    if cached:
        return cached

    try:
        t = yf.Ticker(ticker)
        info = t.info or {}

        # Historial 1 año
        hist = t.history(period="1y")
        closes = hist["Close"] if not hist.empty else pd.Series(dtype=float)

        # Precio actual y variación 1D
        current_price = _safe(info.get("currentPrice") or info.get("regularMarketPrice"))
        prev_close    = _safe(info.get("previousClose") or info.get("regularMarketPreviousClose"))
        if current_price and prev_close and prev_close != 0:
            change_1d     = round(current_price - prev_close, 4)
            change_1d_pct = round((change_1d / prev_close) * 100, 2)
        else:
            change_1d     = None
            change_1d_pct = None

        # Métricas fundamentales
        metrics = {
            "per":              _safe(info.get("trailingPE")),
            "pb":               _safe(info.get("priceToBook")),
            "peg":              _safe(info.get("pegRatio")),
            "ev_ebitda":        _safe(info.get("enterpriseToEbitda")),
            "debt_equity":      _safe(info.get("debtToEquity")),
            "roe":              _safe(info.get("returnOnEquity")),
            "operating_margin": _safe(info.get("operatingMargins")),
            "rsi":              _calc_rsi(closes) if len(closes) > 15 else None,
        }

        score, breakdown = _calc_score(metrics)
        signal = _signal(score)

        # Historial para gráfico
        price_history = []
        if not hist.empty:
            for date, row in hist.iterrows():
                price_history.append({
                    "date":  date.strftime("%Y-%m-%d"),
                    "close": round(float(row["Close"]), 4),
                })

        currency = info.get("currency", "")

        data = {
            "ticker":          ticker,
            "name":            info.get("longName") or info.get("shortName") or ticker,
            "sector":          info.get("sector") or "—",
            "industry":        info.get("industry") or "—",
            "market":          _market_for(ticker),
            "currency":        currency,
            "price":           current_price,
            "change_1d":       change_1d,
            "change_1d_pct":   change_1d_pct,
            "score":           score,
            "signal":          signal,
            "metrics":         metrics,
            "score_breakdown": breakdown,
            "price_history":   price_history,
            "updated_at":      datetime.utcnow().isoformat() + "Z",
        }

        _cache_set(ticker, data)
        return data

    except Exception as e:
        return {
            "ticker":        ticker,
            "name":          ticker,
            "sector":        "—",
            "industry":      "—",
            "market":        _market_for(ticker),
            "currency":      "",
            "price":         None,
            "change_1d":     None,
            "change_1d_pct": None,
            "score":         0,
            "signal":        "NEUTRAL",
            "metrics":       {},
            "score_breakdown": {},
            "price_history": [],
            "updated_at":    datetime.utcnow().isoformat() + "Z",
            "error":         str(e),
        }

# ── API pública ───────────────────────────────────────────────────────────────
def get_all_stocks(tickers: list) -> list:
    """Devuelve lista de dicts con datos básicos + score para cada ticker."""
    results = []
    for ticker in tickers:
        d = _fetch_stock(ticker)
        results.append({
            "ticker":        d["ticker"],
            "name":          d["name"],
            "sector":        d["sector"],
            "market":        d["market"],
            "currency":      d["currency"],
            "price":         d["price"],
            "change_1d":     d["change_1d"],
            "change_1d_pct": d["change_1d_pct"],
            "score":         d["score"],
            "signal":        d["signal"],
            "updated_at":    d["updated_at"],
            "error":         d.get("error"),
        })
    # COMPRAR primero
    order = {"COMPRAR": 0, "NEUTRAL": 1, "VENDER": 2}
    results.sort(key=lambda x: (order.get(x["signal"], 1), -(x["score"] or 0)))
    return results

def get_stock_detail(ticker: str) -> dict:
    """Devuelve el dict completo incluyendo historial de precios y desglose del score."""
    return _fetch_stock(ticker)
