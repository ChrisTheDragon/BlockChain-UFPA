from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Transaction:
    tx_id: str
    origin: str
    destination: str
    value: float
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Transaction":
        return Transaction(
            tx_id=str(data["tx_id"]),
            origin=str(data["origin"]),
            destination=str(data["destination"]),
            value=float(data["value"]),
            timestamp=str(data["timestamp"]),
        )


@dataclass
class Block:
    index: int
    previous_hash: str
    transactions: list[Transaction]
    nonce: int
    timestamp: str
    block_hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "timestamp": self.timestamp,
        }

    def compute_hash(self) -> str:
        encoded = json.dumps(self.payload(), sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        data = self.payload()
        data["block_hash"] = self.block_hash
        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Block":
        transactions = [Transaction.from_dict(tx) for tx in data.get("transactions", [])]
        return Block(
            index=int(data["index"]),
            previous_hash=str(data["previous_hash"]),
            transactions=transactions,
            nonce=int(data["nonce"]),
            timestamp=str(data["timestamp"]),
            block_hash=str(data.get("block_hash", "")),
        )
