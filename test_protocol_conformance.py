#!/usr/bin/env python
"""
Testes de conformidade com o padrão Blockchain LSD 2025
"""

import json
import struct
from src.node import PeerMessage
from src.models import Transaction, Block, current_timestamp


def test_message_format():
    """Testa se o formato de mensagem está correto"""
    print("=" * 60)
    print("TESTE 1: Formato de Mensagem")
    print("=" * 60)
    
    msg = PeerMessage(
        message_type="REQUEST_CHAIN",
        payload={},
        sender="127.0.0.1:5001"
    )
    
    serialized = msg.to_bytes()
    size_bytes = serialized[:4]
    json_bytes = serialized[4:]
    
    size = struct.unpack(">I", size_bytes)[0]
    assert size == len(json_bytes), "Tamanho big-endian incorreto"
    print(f"✅ Tamanho big-endian correto: {size} bytes")
    
    data = json.loads(json_bytes.decode("utf-8"))
    assert "type" in data, "Campo 'type' obrigatório ausente"
    assert "payload" in data, "Campo 'payload' obrigatório ausente"
    assert "sender" in data, "Campo 'sender' obrigatório ausente"
    print("✅ Estrutura JSON válida com campos obrigatórios")
    
    msg2 = PeerMessage.from_bytes(json_bytes)
    assert msg2.message_type == msg.message_type
    assert msg2.payload == msg.payload
    assert msg2.sender == msg.sender
    print("✅ Desserialização idêntica à original")
    print()


def test_transaction_payload():
    """Testa se payloads de transação estão corretos"""
    print("=" * 60)
    print("TESTE 2: Payload NEW_TRANSACTION")
    print("=" * 60)
    
    tx = Transaction(
        id="test-123",
        origem="127.0.0.1:5001",
        destino="127.0.0.1:5002",
        valor=10.5,
        timestamp=current_timestamp()
    )
    
    msg = PeerMessage(
        message_type="NEW_TRANSACTION",
        payload={"transaction": tx.to_dict()},
        sender="127.0.0.1:5001"
    )
    
    serialized = msg.to_bytes()
    msg2 = PeerMessage.from_bytes(serialized[4:])
    
    assert msg2.message_type == "NEW_TRANSACTION"
    assert "transaction" in msg2.payload
    restored_tx = Transaction.from_dict(msg2.payload["transaction"])
    assert restored_tx.id == tx.id
    assert restored_tx.valor == tx.valor
    print("✅ Transação serializada/desserializada corretamente")
    print()


def test_block_payload():
    """Testa se payloads de bloco estão corretos"""
    print("=" * 60)
    print("TESTE 3: Payload NEW_BLOCK")
    print("=" * 60)
    
    block = Block(
        index=1,
        previous_hash="000abc123",
        transactions=[],
        nonce=42,
        timestamp=current_timestamp(),
        hash="000def456"
    )
    
    msg = PeerMessage(
        message_type="NEW_BLOCK",
        payload={"block": block.to_dict()},
        sender="127.0.0.1:5001"
    )
    
    serialized = msg.to_bytes()
    msg2 = PeerMessage.from_bytes(serialized[4:])
    
    assert msg2.message_type == "NEW_BLOCK"
    assert "block" in msg2.payload
    restored_block = Block.from_dict(msg2.payload["block"])
    assert restored_block.index == block.index
    assert restored_block.nonce == block.nonce
    assert restored_block.hash == block.hash
    print("✅ Bloco serializado/desserializado corretamente")
    print()


def test_response_chain_payload():
    """Testa se payload RESPONSE_CHAIN está correto"""
    print("=" * 60)
    print("TESTE 4: Payload RESPONSE_CHAIN")
    print("=" * 60)
    
    payload = {
        "blockchain": {
            "chain": [],
            "pending_transactions": [],
            "peers": ["127.0.0.1:5001", "127.0.0.1:5002"]
        }
    }
    
    msg = PeerMessage(
        message_type="RESPONSE_CHAIN",
        payload=payload,
        sender="127.0.0.1:5001"
    )
    
    serialized = msg.to_bytes()
    msg2 = PeerMessage.from_bytes(serialized[4:])
    
    assert msg2.message_type == "RESPONSE_CHAIN"
    assert "blockchain" in msg2.payload
    assert "chain" in msg2.payload["blockchain"]
    assert "pending_transactions" in msg2.payload["blockchain"]
    assert "peers" in msg2.payload["blockchain"]
    print("✅ RESPONSE_CHAIN com estrutura correta")
    print()


def test_sender_format():
    """Testa se sender está sempre no formato host:porta"""
    print("=" * 60)
    print("TESTE 5: Formato de 'Sender'")
    print("=" * 60)
    
    senders = [
        "127.0.0.1:5001",
        "192.168.1.1:8080",
        "localhost:9999",
    ]
    
    for sender in senders:
        msg = PeerMessage(
            message_type="REQUEST_CHAIN",
            payload={},
            sender=sender
        )
        serialized = msg.to_bytes()
        msg2 = PeerMessage.from_bytes(serialized[4:])
        assert msg2.sender == sender
        print(f"✅ Sender '{sender}' preservado corretamente")
    print()


def test_encoding():
    """Testa se é sempre UTF-8"""
    print("=" * 60)
    print("TESTE 6: Encoding UTF-8")
    print("=" * 60)
    
    msg = PeerMessage(
        message_type="NEW_TRANSACTION",
        payload={
            "transaction": {
                "id": "test-ã-ç-é",
                "origem": "127.0.0.1:5001",
                "destino": "127.0.0.1:5002",
                "valor": 1.0,
                "timestamp": current_timestamp()
            }
        },
        sender="127.0.0.1:5001"
    )
    
    serialized = msg.to_bytes()
    size = struct.unpack(">I", serialized[:4])[0]
    text = serialized[4:4+size].decode("utf-8")
    data = json.loads(text)
    
    assert data["payload"]["transaction"]["id"] == "test-ã-ç-é"
    print("✅ Caracteres especiais preservados em UTF-8")
    print()


if __name__ == "__main__":
    try:
        test_message_format()
        test_transaction_payload()
        test_block_payload()
        test_response_chain_payload()
        test_sender_format()
        test_encoding()
        
        print("=" * 60)
        print("✅ TODOS OS TESTES PASSARAM")
        print("✅ Protocolo em conformidade com Blockchain LSD 2025")
        print("=" * 60)
    except AssertionError as e:
        print(f"❌ TESTE FALHOU: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
