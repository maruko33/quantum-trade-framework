from src.config import get_settings
from src.broker.ibkr import IBKRBroker

if __name__ == "__main__":
    s = get_settings()
    b = IBKRBroker(s)
    b.connect()
    acct = b.get_account()
    print("ACCOUNT:", acct)
    b.disconnect()
