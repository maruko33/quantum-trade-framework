import os
from datetime import datetime, timedelta, timezone
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

load_dotenv()

def must_env(k: str) -> str:
    v = os.getenv(k)
    if not v:
        raise RuntimeError(f"Missing env: {k}")
    return v

if __name__ == "__main__":
    key = must_env("ALPACA_API_KEY_ID")
    secret = must_env("ALPACA_API_SECRET_KEY")

    client = StockHistoricalDataClient(key, secret)  # stock historical client :contentReference[oaicite:8]{index=8}
    start = datetime.now(timezone.utc) - timedelta(days=5)

    req = StockBarsRequest(symbol_or_symbols="SPY", timeframe=TimeFrame.Minute, start=start)
    bars = client.get_stock_bars(req)

    df = bars.df  # pandas multi-index df is supported in examples :contentReference[oaicite:9]{index=9}
    print(df.tail(5))
