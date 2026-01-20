from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol, Literal, Optional, List


Side = Literal["BUY", "SELL"]
OrderType = Literal["MKT", "LMT"]


@dataclass(frozen=True)
class AccountSnapshot:
    account: str
    net_liquidation: float | None
    buying_power: float | None
    currency: str | None


@dataclass(frozen=True)
class PositionSnapshot:
    symbol: str
    qty: float
    avg_cost: float | None
    currency: str | None


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: Side
    qty: float
    order_type: OrderType = "MKT"
    limit_price: Optional[float] = None


@dataclass(frozen=True)
class OrderAck:
    broker_order_id: str
    status: str


class Broker(Protocol):
    def connect(self) -> None: ...
    def disconnect(self) -> None: ...

    def get_account(self) -> AccountSnapshot: ...
    def get_positions(self) -> List[PositionSnapshot]: ...

    def place_order(self, intent: OrderIntent) -> OrderAck: ...
    def get_order_status(self, broker_order_id: str) -> str: ...
