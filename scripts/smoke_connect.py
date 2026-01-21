from src.config import get_settings
from src.broker.ibkr import IBKRBroker

def main():
    s = get_settings()
    broker = IBKRBroker(s)
    try:
        broker.connect()
        print("connected: True")
        print("serverVersion:", broker.ib.client.serverVersion())
    finally:
        broker.disconnect()

if __name__ == "__main__":
    main()
