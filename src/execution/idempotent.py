from __future__ import annotations

from dataclasses import asdict
from typing import Tuple

from src.broker.base import Broker, OrderIntent, OrderAck
from src.store.sqlite_store import SqliteStore


TERMINAL = {"FILLED", "CANCELLED", "INACTIVE"}  # IB common final status


def submit_idempotent(
    *,
    signal_id: str,
    intent: OrderIntent,
    broker: Broker,
    store: SqliteStore,
) -> Tuple[str, str]:
    """
    Returns: (broker_order_id, status)
    """
    existing = store.get_order_by_signal(signal_id)
    if existing and existing.get("broker_order_id"):
        # idempotency：same signal_id place order → not placing additional order
        store.log_event(signal_id, "idempotent_hit", {"existing": existing})
        return existing["broker_order_id"], existing["status"]

    if not existing:
        store.create_order(signal_id, intent, status="CREATED")
        store.log_event(signal_id, "intent_created", asdict(intent))

    ack: OrderAck = broker.place_order(intent)
    store.set_broker_order_id(signal_id, ack.broker_order_id, ack.status)
    store.log_event(signal_id, "order_submitted", {"broker_order_id": ack.broker_order_id, "status": ack.status})

    return ack.broker_order_id, ack.status


def refresh_status(*, signal_id: str, broker, store) -> str:
    row = store.get_order_by_signal(signal_id)
    if not row or not row.get("broker_order_id"):
        raise RuntimeError(f"No broker_order_id found for signal_id={signal_id}")

    current = (row.get("status") or "").strip().upper()

    # 1) 如果 DB 里已经是终态，直接返回（不要再去刷 broker）
    if current in TERMINAL:
        return current

    broker_order_id = row["broker_order_id"]
    st = broker.get_order_status(broker_order_id)
    st_norm = (st or "").strip().upper()

    # 2) 查不到（跨进程 trade 不在内存）→ 不要覆盖 DB
    if st_norm in {"UNKNOWN_ID", "UNKNOWN"}:
        store.log_event(signal_id, "status_unknown", {"broker_order_id": broker_order_id, "kept": current})
        return current or st_norm

    # 3) 正常状态变化：落库
    if st_norm != current:
        store.update_status(signal_id, st_norm)
        store.log_event(signal_id, "status_update", {"from": current, "to": st_norm})

    return st_norm