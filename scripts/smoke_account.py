import os
from alpaca.trading.client import TradingClient
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

    tc = TradingClient(key, secret, paper=paper)  # paper trading via paper=True :contentReference[oaicite:6]{index=6}
    acct = tc.get_account()
    clock = tc.get_clock()  # market clock endpoint :contentReference[oaicite:7]{index=7}

    print("account:", {"equity": acct.equity, "buying_power": acct.buying_power, "status": acct.status})
    print("clock:", {"is_open": clock.is_open, "next_open": clock.next_open, "next_close": clock.next_close})
