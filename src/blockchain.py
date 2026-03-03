from __future__ import annotations

from threading import RLock
from typing import Iterable

from .models import Block, Transaction, utc_now_iso


GENESIS_TIMESTAMP = "2026-01-01T00:00:00+00:00"
GENESIS_NONCE = 0
GENESIS_PREVIOUS_HASH = "0" * 64
DIFFICULTY_PREFIX = "000"
MINING_REWARD = 10.0


class Blockchain:
    def __init__(self, node_address: str) -> None:
        self.node_address = node_address
        self.lock = RLock()
        self.chain: list[Block] = [self._create_genesis_block()]
        self.pending_transactions: list[Transaction] = []
        self.known_transactions: set[str] = set()

    def _create_genesis_block(self) -> Block:
        genesis = Block(
            index=0,
            previous_hash=GENESIS_PREVIOUS_HASH,
            transactions=[],
            nonce=GENESIS_NONCE,
            timestamp=GENESIS_TIMESTAMP,
        )
        genesis.block_hash = genesis.compute_hash()
        return genesis

    @property
    def last_block(self) -> Block:
        return self.chain[-1]

    def get_balance(self, address: str, include_pending: bool = False) -> float:
        balance = 0.0
        for block in self.chain:
            for tx in block.transactions:
                if tx.origin == address:
                    balance -= tx.value
                if tx.destination == address:
                    balance += tx.value

        if include_pending:
            for tx in self.pending_transactions:
                if tx.origin == address:
                    balance -= tx.value
                if tx.destination == address:
                    balance += tx.value

        return round(balance, 8)

    def can_apply_transaction(self, tx: Transaction) -> bool:
        if tx.value <= 0:
            return False
        if tx.origin == "SYSTEM":
            return True
        projected_balance = self.get_balance(tx.origin, include_pending=True)
        return projected_balance >= tx.value

    def add_transaction(self, tx: Transaction) -> bool:
        with self.lock:
            if tx.tx_id in self.known_transactions:
                return False
            if not self.can_apply_transaction(tx):
                return False
            self.pending_transactions.append(tx)
            self.known_transactions.add(tx.tx_id)
            return True

    def _prepare_block(self, transactions: list[Transaction]) -> Block:
        return Block(
            index=self.last_block.index + 1,
            previous_hash=self.last_block.block_hash,
            transactions=transactions,
            nonce=0,
            timestamp=utc_now_iso(),
        )

    def mine_pending_transactions(self) -> Block | None:
        with self.lock:
            if not self.pending_transactions:
                return None

            valid_pool = [tx for tx in self.pending_transactions if self.can_apply_transaction(tx)]
            if not valid_pool:
                self.pending_transactions.clear()
                return None

            reward = Transaction(
                tx_id=f"reward-{self.last_block.index + 1}-{self.node_address}",
                origin="SYSTEM",
                destination=self.node_address,
                value=MINING_REWARD,
                timestamp=utc_now_iso(),
            )
            selected_transactions = [*valid_pool, reward]
            candidate = self._prepare_block(selected_transactions)

        while True:
            candidate_hash = candidate.compute_hash()
            if candidate_hash.startswith(DIFFICULTY_PREFIX):
                candidate.block_hash = candidate_hash
                break
            candidate.nonce += 1

        with self.lock:
            if candidate.previous_hash != self.last_block.block_hash:
                return None
            self.chain.append(candidate)
            included_ids = {tx.tx_id for tx in selected_transactions}
            self.pending_transactions = [tx for tx in self.pending_transactions if tx.tx_id not in included_ids]
            self.known_transactions.update(included_ids)
            return candidate

    def is_valid_block(self, block: Block, previous_block: Block) -> bool:
        if block.index != previous_block.index + 1:
            return False
        if block.previous_hash != previous_block.block_hash:
            return False
        computed = block.compute_hash()
        if block.block_hash != computed:
            return False
        if not block.block_hash.startswith(DIFFICULTY_PREFIX):
            return False

        snapshot_balances: dict[str, float] = {}
        reward_count = 0
        for tx in block.transactions:
            if tx.value <= 0:
                return False
            if tx.origin == "SYSTEM":
                reward_count += 1
                if tx.value != MINING_REWARD:
                    return False
                continue

            if tx.origin not in snapshot_balances:
                snapshot_balances[tx.origin] = self.get_balance(tx.origin)
            if snapshot_balances[tx.origin] < tx.value:
                return False
            snapshot_balances[tx.origin] -= tx.value

        return reward_count <= 1

    def add_block(self, block: Block) -> bool:
        with self.lock:
            if not self.is_valid_block(block, self.last_block):
                return False
            self.chain.append(block)
            included_ids = {tx.tx_id for tx in block.transactions}
            self.pending_transactions = [tx for tx in self.pending_transactions if tx.tx_id not in included_ids]
            self.known_transactions.update(included_ids)
            return True

    def validate_chain(self, chain: Iterable[Block]) -> bool:
        sequence = list(chain)
        if not sequence:
            return False
        if sequence[0].to_dict() != self.chain[0].to_dict():
            return False

        for index in range(1, len(sequence)):
            if not self.is_valid_block(sequence[index], sequence[index - 1]):
                return False
        return True

    def replace_chain(self, new_chain: list[Block]) -> bool:
        with self.lock:
            if len(new_chain) <= len(self.chain):
                return False
            if not self.validate_chain(new_chain):
                return False
            self.chain = new_chain
            existing_ids = {tx.tx_id for block in self.chain for tx in block.transactions}
            self.known_transactions = set(existing_ids)
            self.pending_transactions = [tx for tx in self.pending_transactions if tx.tx_id not in existing_ids]
            return True

    def chain_to_dict(self) -> list[dict]:
        with self.lock:
            return [block.to_dict() for block in self.chain]

    def pending_to_dict(self) -> list[dict]:
        with self.lock:
            return [tx.to_dict() for tx in self.pending_transactions]
