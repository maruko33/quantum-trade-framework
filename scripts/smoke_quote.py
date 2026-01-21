import os

from src.config import get_settings
from src.broker.ibkr import IBKRBroker
from src.market_data.ibkr import IBKRMarketData

def main():
    s = get_settings()
    broker = IBKRBroker(s)

    mkt_type = int(os.getenv("IB_MKT_DATA_TYPE", "1"))
    md = IBKRMarketData(broker, market_data_type=mkt_type)

    try:
        broker.connect()
        q = md.snapshot("SPY")
        print("QUOTE:", q)

        # 如果你看到 None，且 TWS/IBG 报 354：
        # 354 = Not subscribed to requested market data :contentReference[oaicite:10]{index=10}
        # 就去 Portal 订阅 Level 1 market data :contentReference[oaicite:11]{index=11}
    finally:
        broker.disconnect()

if __name__ == "__main__":
    main()
