import time
import uuid

from src.config import get_settings
from src.broker.ibkr import IBKRBroker
from src.broker.base import OrderIntent
from src.store.sqlite_store import SqliteStore
from src.execution.idempotent import submit_idempotent, refresh_status

def main():
    s = get_settings()
    broker = IBKRBroker(s)
    store = SqliteStore("trade_runs.db")

    # you could change signal_id to test idempotency
    signal_id = "smoke_spy_buy_001"
    intent = OrderIntent(symbol="SPY", side="BUY", qty=1, order_type="MKT")

    try:
        broker.connect()

        oid, st = submit_idempotent(signal_id=signal_id, intent=intent, broker=broker, store=store)
        print("idempotent_submit:", {"signal_id": signal_id, "broker_order_id": oid, "status": st})

        # loop to check status（v0.2 仍然足够轻量）
        for _ in range(20):
            st2 = refresh_status(signal_id=signal_id, broker=broker, store=store)
            print("status:", st2)
            if st2 in {"FILLED", "CANCELLED", "INACTIVE", "REJECTED"}:
                break
            time.sleep(0.5)

        # ✅ do a double check（同 signal_id）
        oid2, st3 = submit_idempotent(signal_id=signal_id, intent=intent, broker=broker, store=store)
        print("second_call_should_not_place_new_order:", {"broker_order_id": oid2, "status": st3})

    finally:
        broker.disconnect()

if __name__ == "__main__":
    main()
