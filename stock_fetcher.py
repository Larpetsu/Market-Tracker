import yfinance as yf
from config import MAX_RETRIES
from typing import Dict, Optional
import asyncio

_EXCHANGE_SUFFIXES = {
    "NYSE": "", "NASDAQ": "", "LSE": ".L", "FRA": ".F",
    "PAR": ".PA", "TOK": ".T", "XETRA": ".DE", "HKEX": ".HK",
    "TSX": ".TO", "ASX": ".AX",
}

# Friendly labels for yfinance's raw marketState values
_MARKET_STATE_LABELS = {
    "REGULAR": "🟢 OPEN",
    "PRE": "🟡 PRE-MARKET",
    "PREPRE": "🟡 PRE-MARKET",
    "POST": "🟠 AFTER-HOURS",
    "POSTPOST": "🟠 AFTER-HOURS",
    "CLOSED": "🔴 CLOSED",
}


def _format_ticker(ticker: str, exchange: str) -> str:
    """Appends the Yahoo Finance suffix for the given exchange, if we know one.

    NYSE/NASDAQ tickers don't need a suffix; LSE/TSX/etc do. If the exchange
    isn't recognised we pass the ticker through unchanged rather than guessing.
    """
    if not exchange:
        return ticker
    suffix = _EXCHANGE_SUFFIXES.get(exchange.upper())
    return f"{ticker}{suffix}" if suffix is not None else ticker


async def fetch_market_data(ticker: str, exchange: str = "") -> Optional[Dict]:
    """Fetches a price snapshot for one ticker. Returns None if it can't be found."""
    target_ticker = _format_ticker(ticker, exchange)

    for attempt in range(MAX_RETRIES):
        try:
            stock = yf.Ticker(target_ticker)
            info = await asyncio.get_event_loop().run_in_executor(None, lambda: stock.info)

            if not info or info.get("regularMarketPrice") is None:
                return None

            price = info.get("regularMarketPrice") or info.get("currentPrice")
            change = info.get("regularMarketChange") or 0.0
            percent = (info.get("regularMarketChangePercent") or 0.0) / 100

            return {
                "ticker": ticker.upper(),
                "price": price,
                "currency": info.get("currency", "USD"),
                "change": change,
                "percent": percent,
                "market_status": _MARKET_STATE_LABELS.get(info.get("marketState", ""), "⚪ UNKNOWN"),
                "name": info.get("shortName") or ticker.upper(),
            }
        except Exception:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(2 ** attempt)  # exponential backoff
    return None
