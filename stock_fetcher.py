import yfinance as yf
from config import MAX_RETRIES, REQUEST_TIMEOUT
from typing import Dict, Optional, Tuple
import time
import asyncio

def _format_ticker(ticker: str, exchange: str) -> str:
    if exchange:
        suffix = {
            "NYSE": ".N", "NASDAQ": ".O", "LSE": ".L", 
            "FRA": ".F", "PAR": ".P", "TOK": ".T", "XETRA": ".DE"
        }.get(exchange.upper(), ".Q")
        return f"{ticker}{suffix}"
    return ticker

async def fetch_market_data(ticker: str, exchange: str = "") -> Optional[Dict]:
    target_ticker = _format_ticker(ticker, exchange)
    for attempt in range(MAX_RETRIES):
        try:
            stock = yf.Ticker(target_ticker)
            info = await asyncio.get_event_loop().run_in_executor(
                None, lambda: stock.info
            )
            
            if not info or 'regularMarketPrice' not in info:
                return None

            price = info.get('regularMarketPrice') or info.get('currentPrice')
            change = info.get('regularMarketChange')
            percent = info.get('regularMarketChangePercent', 0) / 100
            
            return {
                "ticker": ticker.upper(),
                "price": price,
                "currency": info.get("currency", "USD"),
                "change": change,
                "percent": percent,
                "market_status": "OPEN" if 9 < int(time.strftime("%H")) < 17 else "CLOSED",
                "name": info.get("shortName", ticker)
            }
        except Exception as e:
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return None
