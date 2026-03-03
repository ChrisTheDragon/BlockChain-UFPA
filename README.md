# Blockchain UFPA - Nó P2P em Python

Implementação de um sistema de **nó blockchain distribuído** sem servidor central, com:

- transações validadas;
- blockchain local por nó;
- Proof of Work simplificado (hash iniciando com `000`);
- propagação de transações e blocos por sockets TCP;
- sincronização de cadeia para entrada tardia de nós.

## Estrutura

- `src/models.py` - modelos de `Transaction` e `Block`
- `src/blockchain.py` - regras da blockchain, validação e mineração
- `src/node.py` - rede P2P, protocolo e sincronização
- `src/cli.py` - interface de linha de comando

## Protocolo de Comunicação (Padrão: Blockchain LSD 2025)

**Formato de Transmissão (TCP:**
```
[4 bytes: tamanho big-endian] [N bytes: JSON UTF-8]
```

**Estrutura das Mensagens:**
```json
{
  "type": "<TIPO>",
  "payload": { ... },
  "sender": "host:porta"
}
```

### 1) `NEW_TRANSACTION`
Propaga uma nova transação válida.

```json
{
  "type": "NEW_TRANSACTION",
  "payload": {
    "transaction": {
      "tx_id": "...",
      "origin": "...",
      "destination": "...",
      "value": 0.0,
      "timestamp": "..."
    }
  },
  "sender": "host:porta"
}
```

### 2) `NEW_BLOCK`
Propaga um bloco minerado.

```json
{
  "type": "NEW_BLOCK",
  "payload": {
    "block": {
      "index": 0,
      "previous_hash": "...",
      "transactions": [...],
      "nonce": 0,
      "timestamp": "...",
      "block_hash": "..."
    }
  },
  "sender": "host:porta"
}
```

### 3) `REQUEST_CHAIN`
Solicita a blockchain completa (sincronização).

```json
{
  "type": "REQUEST_CHAIN",
  "payload": {},
  "sender": "host:porta"
}
```

### 4) `RESPONSE_CHAIN`
Resposta com blockchain, transações pendentes e peers conhecidos.

```json
{
  "type": "RESPONSE_CHAIN",
  "payload": {
    "blockchain": {
      "chain": [...],
      "pending_transactions": [...],
      "peers": ["host1:porta1", "host2:porta2"]
    }
  },
  "sender": "host:porta"
}
```

## Regras implementadas

### Transações
- valor deve ser positivo (`value > 0`)
- não permite saldo negativo
- cada transação tem id único (`tx_id`) e timestamp

### Blocos
- contém índice, hash anterior, transações, nonce, timestamp e hash atual
- hash com SHA-256
- bloco só é válido se `block_hash` inicia com `000`

### Blockchain
- bloco gênesis fixo
- encadeamento por `previous_hash`
- validação completa de cadeia
- substituição por cadeia remota maior e válida

## Como executar

Requisitos: Python 3.11+.

No terminal, dentro da pasta do projeto:

```bash
python -m src.cli --port 5001
```

Em outro terminal, suba outro nó conhecendo o primeiro:

```bash
python -m src.cli --port 5002 --peer 127.0.0.1:5001
```

Opcionalmente um terceiro nó:

```bash
python -m src.cli --port 5003 --peer 127.0.0.1:5001
```

## Comandos da CLI

- `mine` -> minera blockchain
- `balance` -> ver seu saldo
- `txs` -> ver transações pendentes
- `peers` -> ver outros nós
- `send <host:porta> <valor>` -> mandar cripto
- `sync` -> sincronizar blockchain
- `chain` -> ver blockchain local
- `exit` -> encerrar

## Checklist (coberto)

- [x] Criação da estrutura básica do nó
- [x] Comunicação entre processos via sockets
- [x] Implementação da estrutura de bloco
- [x] Implementação da blockchain local
- [x] Validação da cadeia
- [x] Implementação de transações
- [x] Pool de transações
- [x] Propagação de transações entre nós
- [x] Implementação do Proof of Work
- [x] Criação e propagação de blocos
- [x] Aceitação de blocos remotos
- [x] Entrada tardia de nós na rede
- [x] Sincronização da blockchain

## Observação sobre integração com outros grupos

O protocolo acima está documentado e usa os 4 tipos de mensagem exigidos no enunciado. Para compatibilidade com o PDF acordado entre grupos, mantenha os mesmos nomes e estrutura de campos (`type`, `data`, `sender`) em todos os nós participantes.
