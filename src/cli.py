from __future__ import annotations

import argparse
import json

from .node import Node


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Nó blockchain P2P (UFPA)")
    parser.add_argument("--host", default="127.0.0.1", help="Host local do nó")
    parser.add_argument("--port", type=int, required=True, help="Porta do nó")
    parser.add_argument(
        "--peer",
        action="append",
        default=[],
        help="Nó conhecido no formato host:porta (pode repetir)",
    )
    return parser


def print_help() -> None:
    print("\nComandos:")
    print("  help                           -> mostra esta ajuda")
    print("  mine                           -> minera um novo bloco")
    print("  balance                        -> mostra seu saldo")
    print("  send <host:porta> <valor>      -> envia cripto")
    print("  txs                            -> mostra transações pendentes")
    print("  chain                          -> mostra blockchain local")
    print("  peers                          -> lista nós conhecidos")
    print("  sync                           -> sincroniza com outros nós")
    print("  exit                           -> encerra o nó\n")


def interactive_loop(node: Node) -> None:
    print(f"Nó ativo em {node.address}")
    print_help()

    while True:
        try:
            command = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando...")
            break

        if not command:
            continue

        parts = command.split()
        action = parts[0].lower()

        if action == "help":
            print_help()
            continue

        if action == "mine":
            ok, result = node.mine()
            if ok:
                # Alterado de result.block_hash para result.hash
                print(f"Bloco minerado e propagado: índice={result.index}, hash={result.hash}")
            else:
                print(result)
            continue

        if action == "balance":
            print(f"Saldo de {node.address}: {node.get_balance()}")
            continue

        if action == "send":
            if len(parts) != 3:
                print("Uso: send <host:porta> <valor>")
                continue
            destination = parts[1]
            try:
                value = float(parts[2])
            except ValueError:
                print("Valor inválido.")
                continue

            ok, result = node.create_transaction(destination, value)
            if ok:
                # Alterado de result.tx_id para result.id
                print(f"Transação enviada: {result.id}")
            else:
                print(result)
            continue

        if action == "txs":
            print(json.dumps(node.get_pending(), indent=2, ensure_ascii=False))
            continue

        if action == "chain":
            print(json.dumps(node.get_chain(), indent=2, ensure_ascii=False))
            continue

        if action == "peers":
            peers = node.list_peers()
            print("Nós conhecidos:")
            for peer in peers:
                print(f" - {peer}")
            if not peers:
                print(" (nenhum)")
            continue

        if action == "sync":
            node.sync_with_network()
            print("Sincronização concluída.")
            continue

        if action == "exit":
            print("Encerrando...")
            break

        print("Comando desconhecido. Digite 'help'.")


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    node = Node(host=args.host, port=args.port, peers=args.peer)
    node.start()
    try:
        interactive_loop(node)
    finally:
        node.stop()


if __name__ == "__main__":
    main()
