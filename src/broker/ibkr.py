from __future__ import annotations

import time
from dataclasses import asdict
from typing import List, Optional

from ib_insync import IB, Stock, MarketOrder, LimitOrder, Trade
from src.config import Settings
from src.broker.base import Broker, AccountSnapshot, PositionSnapshot, OrderIntent, OrderAck


class IBKRBroker(Broker):
    """
    Route A: TWS / IB Gateway (socket) via ib_insync.
    重点：我们用 TRADING_MODE + 端口 做硬保护，避免误连 live。
    """

    def __init__(self, settings: Settings):
        self.s = settings
        self.ib = IB()
        self._connected = False
        self._trades_by_id: dict[str, Trade] = {}

    def _assert_paper_guard(self) -> None:
        # 你可以把“只允许 paper 端口”写死得更严格
        paper_ports = {7497, 4002}
        if self.s.trading_mode != "PAPER":
            raise RuntimeError(f"Refuse to run: TRADING_MODE={self.s.trading_mode} (must be PAPER)")
        if self.s.ib_port not in paper_ports:
            raise RuntimeError(
                f"Refuse to run: IB_PORT={self.s.ib_port} not in paper ports {sorted(paper_ports)}"
            )

    def connect(self) -> None:
        self._assert_paper_guard()
        if self._connected:
            return
        self.ib.connect(self.s.ib_host, self.s.ib_port, clientId=self.s.ib_client_id, timeout=5)
        self._connected = True

    def disconnect(self) -> None:
        if self._connected:
            self.ib.disconnect()
        self._connected = False

    def get_account(self) -> AccountSnapshot:
        self.connect()
        rows = self.ib.accountSummary()
        # rows: list[TagValue] with fields: account, tag, value, currency
        account = rows[0].account if rows else "UNKNOWN"

        def pick(tag: str) -> tuple[Optional[float], Optional[str]]:
            for r in rows:
                if r.tag == tag:
                    try:
                        return float(r.value), r.currency
                    except Exception:
                        return None, r.currency
            return None, None

        netliq, c1 = pick("NetLiquidation")
        bp, c2 = pick("BuyingPower")
        currency = c1 or c2
        return AccountSnapshot(account=account, net_liquidation=netliq, buying_power=bp, currency=currency)

    def get_positions(self) -> List[PositionSnapshot]:
        self.connect()
        ps = []
        for p in self.ib.positions():
            sym = getattr(p.contract, "symbol", "UNKNOWN")
            cur = getattr(p.contract, "currency", None)
            ps.append(PositionSnapshot(symbol=sym, qty=float(p.position), avg_cost=float(p.avgCost) if p.avgCost else None, currency=cur))
        return ps

    def place_order(self, intent: OrderIntent) -> OrderAck:
        self.connect()
        self._assert_paper_guard()

        contract = Stock(intent.symbol, "SMART", "USD")
        self.ib.qualifyContracts(contract)

        if intent.order_type == "MKT":
            order = MarketOrder(intent.side, intent.qty)
        elif intent.order_type == "LMT":
            if intent.limit_price is None:
                raise ValueError("limit_price is required for LMT")
            order = LimitOrder(intent.side, intent.qty, intent.limit_price)
        else:
            raise ValueError(f"Unsupported order_type: {intent.order_type}")

        order.tif = "DAY"
        trade = self.ib.placeOrder(contract, order)

        
        deadline = time.time() + 3.0
        while True:
            order_id = getattr(trade.order, "orderId", 0) or 0
            perm_id = getattr(trade.order, "permId", 0) or 0
            if order_id != 0 or perm_id != 0:
                break
            if time.time() > deadline:
                break
            self.ib.sleep(0.2)

        
        order_id = getattr(trade.order, "orderId", 0) or 0
        perm_id = getattr(trade.order, "permId", 0) or 0
        broker_id = str(perm_id if perm_id != 0 else order_id)

        status = trade.orderStatus.status if trade.orderStatus else "UNKNOWN"
        self._trades_by_id[broker_id] = trade
        return OrderAck(broker_order_id=broker_id, status=status)

    def get_order_status(self, broker_order_id: str) -> str:
        self.connect()
        trade = self._trades_by_id.get(broker_order_id)
        if not trade:
            return "UNKNOWN_ID"
        self.ib.sleep(0.2)
        return trade.orderStatus.status if trade.orderStatus else "UNKNOWN"

    # v0.1 里够用：如果你需要“等成交”，在 smoke 里做轮询即可
    def wait_until_done(self, broker_order_id: str, timeout_s: int = 10) -> str:
        end = time.time() + timeout_s
        while time.time() < end:
            st = self.get_order_status(broker_order_id)
            if st in {"Filled", "Cancelled", "Inactive"}:
                return st
            self.ib.sleep(0.5)
        return self.get_order_status(broker_order_id)
