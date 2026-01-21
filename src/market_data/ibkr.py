from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Optional

from ib_insync import Stock
from src.broker.ibkr import IBKRBroker


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: Optional[float]
    ask: Optional[float]
    last: Optional[float]
    mid: Optional[float]


class IBKRMarketData:
    def __init__(self, broker: IBKRBroker, market_data_type: int = 1):
        self.broker = broker
        self.ib = broker.ib
        self.market_data_type = market_data_type

    def set_market_data_type(self) -> None:
        # IB API: 1 real-time, 3 delayed, 4 delayed-frozen :contentReference[oaicite:8]{index=8}
        try:
            self.ib.reqMarketDataType(self.market_data_type)
        except AttributeError:
            # fallback if wrapper differs
            self.ib.client.reqMarketDataType(self.market_data_type)

    def snapshot(self, symbol: str, timeout_s: float = 5.0) -> Quote:
        self.broker.connect()
        self.set_market_data_type()

        contract = Stock(symbol, "SMART", "USD")
        self.ib.qualifyContracts(contract)

        def _on_error(reqId, errorCode, errorString, contract):
            print("IB_ERROR:", reqId, errorCode, errorString)

        self.ib.errorEvent += _on_error
        # reqMktData supports snapshot=True in ib_insync :contentReference[oaicite:9]{index=9}
        ticker = self.ib.reqMktData(contract, snapshot=True)
        deadline = time.time() + timeout_s

        # wait until ticker gets populated
        while time.time() < deadline:
            last = ticker.last
            bid = ticker.bid
            ask = ticker.ask
            if last is not None or (bid is not None and ask is not None):
                break
            self.ib.sleep(0.1)

        bid = ticker.bid
        ask = ticker.ask
        last = ticker.last
        mid = (bid + ask) / 2 if (bid is not None and ask is not None) else None
        return Quote(symbol=symbol, bid=bid, ask=ask, last=last, mid=mid)
