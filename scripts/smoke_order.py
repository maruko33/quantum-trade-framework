from src.config import get_settings
from src.broker.ibkr import IBKRBroker
from src.broker.base import OrderIntent

def main():
    s = get_settings()
    broker = IBKRBroker(s)
    try:
        broker.connect()

        ack = broker.place_order(OrderIntent(
            symbol="SPY",
            side="BUY",
            qty=1,
            order_type="MKT",
        ))
        print("submitted:", ack.broker_order_id, ack.status)

        # 轮询几次看状态变化（v0.1 足够）
        for _ in range(10):
            st = broker.get_order_status(ack.broker_order_id)
            print("status:", st)
            if st in {"Filled", "Cancelled", "Inactive"}:
                break
            broker.ib.sleep(0.5)
    finally:
        broker.disconnect()

if __name__ == "__main__":
    main()
