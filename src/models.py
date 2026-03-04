from __future__ import annotations

from dataclasses import dataclass, asdict
import hashlib
import json
import time
from typing import Any


def current_timestamp() -> float:
    return time.time()


@dataclass(frozen=True)
class Transaction:
    id: str
    origem: str
    destino: str
    valor: float
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Transaction":
        return Transaction(
            id=str(data["id"]),
            origem=str(data["origem"]),
            destino=str(data["destino"]),
            valor=float(data["valor"]),
            timestamp=float(data["timestamp"]),
        )


@dataclass
class Block:
    index: int
    previous_hash: str
    transactions: list[Transaction]
    nonce: int
    timestamp: float
    hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "nonce": self.nonce,
            "timestamp": self.timestamp,
        }

    def compute_hash(self) -> str:
        # A remoção dos separators garante o espaçamento padrão do Python exigido para bater o hash Gênesis
        encoded = json.dumps(self.payload(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        data = self.payload()
        data["hash"] = self.hash
        return data

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Block":
        transactions = [Transaction.from_dict(tx) for tx in data.get("transactions", [])]
        return Block(
            index=int(data["index"]),
            previous_hash=str(data["previous_hash"]),
            transactions=transactions,
            nonce=int(data["nonce"]),
            timestamp=float(data["timestamp"]),
            hash=str(data.get("hash", "")),
        )
