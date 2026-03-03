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

## Protocolo de Comunicação (JSON/TCP)

Cada mensagem é um JSON em uma linha (`\n` no final):

```json
{
  "type": "NEW_TRANSACTION | NEW_BLOCK | REQUEST_CHAIN | RESPONSE_CHAIN",
  "data": { ... },
  "sender": "host:porta"
}
```

### 1) `NEW_TRANSACTION`
Usada para propagar uma nova transação válida.

- `data` contém os campos da transação:
  - `tx_id`, `origin`, `destination`, `value`, `timestamp`

### 2) `NEW_BLOCK`
Usada para propagar um bloco minerado.

- `data` contém o bloco completo:
  - `index`, `previous_hash`, `transactions`, `nonce`, `timestamp`, `block_hash`

### 3) `REQUEST_CHAIN`
Usada para solicitar a blockchain completa de um nó remoto.

- `data`: `{}`

### 4) `RESPONSE_CHAIN`
Resposta para sincronização de nós.

- `data` contém:
  - `chain`: lista completa de blocos
  - `pending_transactions`: lista de transações pendentes
  - `peers`: lista de nós conhecidos

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
