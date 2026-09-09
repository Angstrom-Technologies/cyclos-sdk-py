"""CLI entry point for angstrom-cyclos."""

from __future__ import annotations

import argparse
import sys

from angstrom_cyclos import CyclosClient, CyclosConfig


def _sync_main(args: argparse.Namespace) -> int:
    config = CyclosConfig.from_env()
    with CyclosClient(config) as client:
        if args.command == "auth" and args.subcommand == "login":
            print("Use application code or environment variables to authenticate.")
            return 0
        if args.command == "members" and args.subcommand == "get":
            member = client.members.get(args.id)
            print(member.model_dump_json(indent=2))
            return 0
        if args.command == "members" and args.subcommand == "search":
            result = client.members.search(query=args.query)
            print(result.model_dump_json(indent=2))
            return 0
        if args.command == "accounts" and args.subcommand == "balance":
            balance = client.accounts.get_balance(args.member)
            print(balance.model_dump_json(indent=2))
            return 0
        if args.command == "transfers" and args.subcommand == "get":
            transfer = client.transfers.get(args.id)
            print(transfer.model_dump_json(indent=2))
            return 0
        if args.command == "transfers" and args.subcommand == "history":
            history = client.transfers.history(
                member_id=args.member, account_type=args.account_type
            )
            print(history.model_dump_json(indent=2))
            return 0
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cyclos", description="Angstrom Cyclos SDK CLI")
    sub = parser.add_subparsers(dest="command")

    auth = sub.add_parser("auth")
    auth.add_subparsers(dest="subcommand").add_parser("login")

    members = sub.add_parser("members")
    members_sub = members.add_subparsers(dest="subcommand")
    get_member = members_sub.add_parser("get")
    get_member.add_argument("id")
    search_member = members_sub.add_parser("search")
    search_member.add_argument("query")

    accounts = sub.add_parser("accounts")
    accounts_sub = accounts.add_subparsers(dest="subcommand")
    balance = accounts_sub.add_parser("balance")
    balance.add_argument("member")

    transfers = sub.add_parser("transfers")
    transfers_sub = transfers.add_subparsers(dest="subcommand")
    get_transfer = transfers_sub.add_parser("get")
    get_transfer.add_argument("id")
    history = transfers_sub.add_parser("history")
    history.add_argument("member")
    history.add_argument("--account-type", default="mobileWallet")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    return _sync_main(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
