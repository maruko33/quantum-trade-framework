import os
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
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
    paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"

    tc = TradingClient(key, secret, paper=paper)  # :contentReference[oaicite:10]{index=10}

    order_req = MarketOrderRequest(
        symbol="SPY",
        qty=1,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    )
    order = tc.submit_order(order_data=order_req)  # order request objects :contentReference[oaicite:11]{index=11}
    print("submitted:", order.id, order.status)

    fetched = tc.get_order_by_id(order.id)
    print("fetched:", fetched.id, fetched.status, fetched.filled_qty, fetched.filled_avg_price)
