import os
from src.config import get_settings
from src.broker.ibkr import IBKRBroker


if __name__ == "__main__":
    s = get_settings()
    b = IBKRBroker(s)
    b.connect()
    positions = b.get_positions()
    print("POSITIONS:")
    for p in positions:
        print(" -", p)
    b.disconnect()
