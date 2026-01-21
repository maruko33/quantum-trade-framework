from src.config import get_settings
from src.broker.ibkr import IBKRBroker

if __name__ == "__main__":
    b = IBKRBroker(get_settings())
    try:
        b.connect()
        acct = b.get_account()
        print("ACCOUNT:", acct)
    finally:
        b.disconnect()
