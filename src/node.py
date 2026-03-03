from __future__ import annotations

from dataclasses import dataclass
import json
import socket
from threading import Thread
from typing import Any

from .blockchain import Blockchain
from .models import Block, Transaction, utc_now_iso


@dataclass
class PeerMessage:
    message_type: str
    data: dict[str, Any]
    sender: str

    def to_json(self) -> bytes:
        payload = {
            "type": self.message_type,
            "data": self.data,
            "sender": self.sender,
        }
        return (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")

    @staticmethod
    def from_json(raw: bytes) -> "PeerMessage":
        payload = json.loads(raw.decode("utf-8"))
        return PeerMessage(
            message_type=str(payload["type"]),
            data=dict(payload.get("data", {})),
            sender=str(payload.get("sender", "unknown")),
        )


class Node:
    def __init__(self, host: str, port: int, peers: list[str] | None = None) -> None:
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"
        self.blockchain = Blockchain(node_address=self.address)
        self.peers: set[str] = set(peers or [])
        self.peers.discard(self.address)
        self.server_socket: socket.socket | None = None
        self.running = False

    def start(self) -> None:
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(20)

        Thread(target=self._accept_loop, daemon=True).start()
        self.sync_with_network()

    def stop(self) -> None:
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass

    def _accept_loop(self) -> None:
        if not self.server_socket:
            return

        while self.running:
            try:
                conn, _ = self.server_socket.accept()
                Thread(target=self._handle_connection, args=(conn,), daemon=True).start()
            except OSError:
                break

    def _handle_connection(self, conn: socket.socket) -> None:
        with conn:
            try:
                raw = self._recv_full_message(conn)
                if not raw:
                    return
                message = PeerMessage.from_json(raw)
                response = self._handle_message(message)
                if response is not None:
                    conn.sendall(response.to_json())
            except (json.JSONDecodeError, KeyError, ValueError):
                return

    def _recv_full_message(self, conn: socket.socket) -> bytes:
        chunks = []
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if b"\n" in chunk:
                break
        payload = b"".join(chunks)
        if b"\n" in payload:
            payload = payload.split(b"\n", 1)[0]
        return payload

    def _send_message(self, peer: str, message: PeerMessage, expect_response: bool = False) -> PeerMessage | None:
        host, port_raw = peer.split(":")
        with socket.create_connection((host, int(port_raw)), timeout=3) as conn:
            conn.sendall(message.to_json())
            if expect_response:
                raw = self._recv_full_message(conn)
                if not raw:
                    return None
                return PeerMessage.from_json(raw)
        return None

    def _broadcast(self, message: PeerMessage) -> None:
        bad_peers: list[str] = []
        for peer in list(self.peers):
            try:
                self._send_message(peer, message)
            except OSError:
                bad_peers.append(peer)

        for bad in bad_peers:
            self.peers.discard(bad)

    def _handle_message(self, message: PeerMessage) -> PeerMessage | None:
        if message.sender != self.address:
            self.peers.add(message.sender)

        if message.message_type == "NEW_TRANSACTION":
            tx = Transaction.from_dict(message.data)
            accepted = self.blockchain.add_transaction(tx)
            if accepted:
                self._broadcast(
                    PeerMessage(
                        message_type="NEW_TRANSACTION",
                        data=tx.to_dict(),
                        sender=self.address,
                    )
                )
            return None

        if message.message_type == "NEW_BLOCK":
            block = Block.from_dict(message.data)
            accepted = self.blockchain.add_block(block)
            if accepted:
                self._broadcast(
                    PeerMessage(
                        message_type="NEW_BLOCK",
                        data=block.to_dict(),
                        sender=self.address,
                    )
                )
            else:
                self.sync_with_network()
            return None

        if message.message_type == "REQUEST_CHAIN":
            payload = {
                "chain": self.blockchain.chain_to_dict(),
                "pending_transactions": self.blockchain.pending_to_dict(),
                "peers": sorted(self.peers | {self.address}),
            }
            return PeerMessage(message_type="RESPONSE_CHAIN", data=payload, sender=self.address)

        if message.message_type == "RESPONSE_CHAIN":
            return None

        return None

    def sync_with_network(self) -> None:
        best_chain: list[Block] | None = None
        collected_peers: set[str] = set()

        request = PeerMessage(message_type="REQUEST_CHAIN", data={}, sender=self.address)
        for peer in list(self.peers):
            try:
                response = self._send_message(peer, request, expect_response=True)
                if not response or response.message_type != "RESPONSE_CHAIN":
                    continue
                remote_chain = [Block.from_dict(raw) for raw in response.data.get("chain", [])]
                remote_peers = set(response.data.get("peers", []))
                collected_peers.update(remote_peers)

                if not remote_chain:
                    continue

                if best_chain is None or len(remote_chain) > len(best_chain):
                    best_chain = remote_chain
            except OSError:
                self.peers.discard(peer)

        self.peers.update(collected_peers)
        self.peers.discard(self.address)

        if best_chain:
            self.blockchain.replace_chain(best_chain)

    def create_transaction(self, destination: str, value: float) -> tuple[bool, str | Transaction]:
        tx = Transaction(
            tx_id=f"{self.address}-{utc_now_iso()}",
            origin=self.address,
            destination=destination,
            value=value,
            timestamp=utc_now_iso(),
        )
        if not self.blockchain.add_transaction(tx):
            return False, "Transação inválida (valor <= 0 ou saldo insuficiente)."

        self._broadcast(PeerMessage(message_type="NEW_TRANSACTION", data=tx.to_dict(), sender=self.address))
        return True, tx

    def mine(self) -> tuple[bool, str | Block]:
        block = self.blockchain.mine_pending_transactions()
        if block is None:
            return False, "Nenhuma transação pendente para minerar ou cadeia mudou durante a mineração."

        self._broadcast(PeerMessage(message_type="NEW_BLOCK", data=block.to_dict(), sender=self.address))
        return True, block

    def list_peers(self) -> list[str]:
        return sorted(self.peers)

    def get_chain(self) -> list[dict[str, Any]]:
        return self.blockchain.chain_to_dict()

    def get_pending(self) -> list[dict[str, Any]]:
        return self.blockchain.pending_to_dict()

    def get_balance(self) -> float:
        return self.blockchain.get_balance(self.address, include_pending=True)
