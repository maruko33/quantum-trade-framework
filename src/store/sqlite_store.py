from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Optional

from src.broker.base import OrderIntent


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SqliteStore:
    def __init__(self, path: str = "trade_runs.db"):
        self.path = path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    signal_id TEXT PRIMARY KEY,
                    broker_order_id TEXT,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    qty REAL NOT NULL,
                    order_type TEXT NOT NULL,
                    limit_price REAL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS order_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    signal_id TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )

    def get_order_by_signal(self, signal_id: str) -> Optional[dict[str, Any]]:
        with self._connect() as con:
            cur = con.execute(
                "SELECT signal_id, broker_order_id, symbol, side, qty, order_type, limit_price, status, created_at, updated_at "
                "FROM orders WHERE signal_id = ?",
                (signal_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            keys = ["signal_id", "broker_order_id", "symbol", "side", "qty", "order_type", "limit_price", "status", "created_at", "updated_at"]
            return dict(zip(keys, row))

    def create_order(self, signal_id: str, intent: OrderIntent, status: str = "CREATED") -> None:
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO orders(signal_id, broker_order_id, symbol, side, qty, order_type, limit_price, status, created_at, updated_at)
                VALUES(?, NULL, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal_id,
                    intent.symbol,
                    intent.side,
                    float(intent.qty),
                    intent.order_type,
                    float(intent.limit_price) if intent.limit_price is not None else None,
                    status,
                    utc_now(),
                    utc_now(),
                ),
            )

    def set_broker_order_id(self, signal_id: str, broker_order_id: str, status: str) -> None:
        with self._connect() as con:
            con.execute(
                "UPDATE orders SET broker_order_id=?, status=?, updated_at=? WHERE signal_id=?",
                (broker_order_id, status, utc_now(), signal_id),
            )

    def update_status(self, signal_id: str, status: str) -> None:
        with self._connect() as con:
            con.execute(
                "UPDATE orders SET status=?, updated_at=? WHERE signal_id=?",
                (status, utc_now(), signal_id),
            )

    def log_event(self, signal_id: str, kind: str, payload: dict[str, Any]) -> None:
        with self._connect() as con:
            con.execute(
                "INSERT INTO order_events(signal_id, ts, kind, payload) VALUES(?, ?, ?, ?)",
                (signal_id, utc_now(), kind, json.dumps(payload, ensure_ascii=False)),
            )
