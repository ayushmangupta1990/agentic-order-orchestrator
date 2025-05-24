"""Deterministic supervisor-worker order orchestration reference implementation."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from typing import Any, Callable


class Stage(str, Enum):
    RECEIVED = "received"
    VALIDATED = "validated"
    RESERVED = "reserved"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    REJECTED = "rejected"


@dataclass
class OrderState:
    order_id: str
    sku: str
    quantity: int
    postal_code: str
    stage: Stage = Stage.RECEIVED
    reservation_id: str | None = None
    dispatch_id: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, worker: str, detail: str) -> None:
        self.events.append({"sequence": len(self.events) + 1, "worker": worker, "detail": detail})


class InMemoryIdempotencyStore:
    def __init__(self) -> None:
        self._results: dict[str, OrderState] = {}

    def get(self, key: str) -> OrderState | None:
        return self._results.get(key)

    def put(self, key: str, value: OrderState) -> None:
        self._results[key] = value


Worker = Callable[[OrderState], OrderState]


class OrderSupervisor:
    """Runs bounded workers and caches the terminal state by payload hash."""

    def __init__(self, stock: dict[str, int], store: InMemoryIdempotencyStore | None = None):
        self.stock = stock
        self.store = store or InMemoryIdempotencyStore()
        self.workers: tuple[Worker, ...] = (self.validate, self.reserve, self.dispatch, self.complete)

    @staticmethod
    def idempotency_key(state: OrderState) -> str:
        payload = f"{state.order_id}|{state.sku}|{state.quantity}|{state.postal_code}"
        return sha256(payload.encode()).hexdigest()

    def run(self, state: OrderState) -> OrderState:
        key = self.idempotency_key(state)
        cached = self.store.get(key)
        if cached:
            return cached
        for worker in self.workers:
            state = worker(state)
            if state.stage is Stage.REJECTED:
                break
        self.store.put(key, state)
        return state

    def validate(self, state: OrderState) -> OrderState:
        if state.quantity <= 0 or not state.sku or len(state.postal_code) < 5:
            state.stage = Stage.REJECTED
            state.record("validation", "invalid order payload")
        else:
            state.stage = Stage.VALIDATED
            state.record("validation", "payload accepted")
        return state

    def reserve(self, state: OrderState) -> OrderState:
        available = self.stock.get(state.sku, 0)
        if available < state.quantity:
            state.stage = Stage.REJECTED
            state.record("inventory", f"insufficient stock: {available} available")
            return state
        self.stock[state.sku] = available - state.quantity
        state.reservation_id = f"res-{state.order_id}"
        state.stage = Stage.RESERVED
        state.record("inventory", f"reserved {state.quantity} unit(s)")
        return state

    @staticmethod
    def dispatch(state: OrderState) -> OrderState:
        state.dispatch_id = f"dsp-{state.postal_code}-{state.order_id}"
        state.stage = Stage.DISPATCHED
        state.record("logistics", "dispatch assigned")
        return state

    @staticmethod
    def complete(state: OrderState) -> OrderState:
        state.stage = Stage.COMPLETED
        state.record("notification", "customer notification prepared")
        return state


if __name__ == "__main__":
    supervisor = OrderSupervisor({"SKU-101": 8})
    result = supervisor.run(OrderState("ORD-001", "SKU-101", 2, "400001"))
    print(result)
