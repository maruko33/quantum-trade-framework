from src.config import get_settings
from src.broker.ibkr import IBKRBroker
from src.broker.base import OrderIntent

if __name__ == "__main__":
    s = get_settings()
    b = IBKRBroker(s)
    b.connect()

    # 先用一个“非常小”的 qty 做 paper 测试
    intent = OrderIntent(symbol="SPY", side="BUY", qty=1, order_type="MKT")
    ack = b.place_order(intent)
    print("SUBMITTED:", ack)

    # 等一会儿看状态变化
    final_st = b.wait_until_done(ack.broker_order_id, timeout_s=15)
    print("FINAL STATUS:", final_st)

    b.disconnect()
