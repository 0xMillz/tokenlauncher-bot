#!/usr/bin/env python3
"""Token Launcher Bot - CLI for the Token Launcher API."""

from __future__ import annotations

import argparse
import json
import os
import sys

from dotenv import load_dotenv

from tokenlauncher.bot import TokenLauncherBot
from tokenlauncher.client import TokenLauncherError

load_dotenv()


def _print_json(data: dict) -> None:
    print(json.dumps(data, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Token Launcher Bot - Launch and manage tokens on Base chain"
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("TOKEN_LAUNCHER_API_KEY"),
        help="API key (or set TOKEN_LAUNCHER_API_KEY)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # launch
    launch_parser = subparsers.add_parser("launch", help="Launch a new token with liquidity pool")
    launch_parser.add_argument("name", help="Token name")
    launch_parser.add_argument("symbol", help="Token symbol")
    launch_parser.add_argument("--description", help="Token description")
    launch_parser.add_argument("--image-url", help="Token image URL")
    launch_parser.add_argument("--website", help="Token website URL")
    launch_parser.add_argument("--twitter", help="Twitter URL")
    launch_parser.add_argument("--telegram", help="Telegram URL")
    launch_parser.add_argument("--extra", type=json.loads, help='Extra params as JSON, e.g. {"key":"value"}')

    # boost-price
    bp_parser = subparsers.add_parser("boost-price", help="Boost token price")
    bp_parser.add_argument("token_address", help="Token contract address")
    bp_parser.add_argument("--extra", type=json.loads, help='Extra params as JSON')

    # boost-volume
    bv_parser = subparsers.add_parser("boost-volume", help="Generate trading volume")
    bv_parser.add_argument("token_address", help="Token contract address")
    bv_parser.add_argument("--extra", type=json.loads, help='Extra params as JSON')

    # boost-holders
    bh_parser = subparsers.add_parser("boost-holders", help="Increase holder count")
    bh_parser.add_argument("token_address", help="Token contract address")
    bh_parser.add_argument("--extra", type=json.loads, help='Extra params as JSON')

    # withdraw
    withdraw_parser = subparsers.add_parser("withdraw", help="Withdraw tokens from internal wallet")
    withdraw_parser.add_argument("token_address", help="Token contract address")
    withdraw_parser.add_argument("--extra", type=json.loads, help='Extra params as JSON')

    # token-info
    info_parser = subparsers.add_parser("token-info", help="Get public token info")
    info_parser.add_argument("token_address", help="Token contract address")

    # internal-wallets
    wallets_parser = subparsers.add_parser(
        "internal-wallets", help="Get internal wallets holding a token"
    )
    wallets_parser.add_argument("token_address", help="Token contract address")

    # list
    list_parser = subparsers.add_parser("list", help="List all launched token addresses")

    # tokens (metadata)
    tokens_parser = subparsers.add_parser("tokens", help="Get full token metadata by addresses")
    tokens_parser.add_argument(
        "addresses",
        nargs="*",
        help="Token addresses (optional; if omitted, may return all)",
    )

    args = parser.parse_args()
    bot = TokenLauncherBot(api_key=args.api_key)

    try:
        if args.command == "launch":
            extra = args.extra or {}
            if args.description:
                extra["description"] = args.description
            if args.image_url:
                extra["imageUrl"] = args.image_url
            if args.website:
                extra["website"] = args.website
            if args.twitter:
                extra["twitter"] = args.twitter
            if args.telegram:
                extra["telegram"] = args.telegram
            result = bot.launch(args.name, args.symbol, **extra)
        elif args.command == "boost-price":
            result = bot.boost_price(args.token_address, **(args.extra or {}))
        elif args.command == "boost-volume":
            result = bot.boost_volume(args.token_address, **(args.extra or {}))
        elif args.command == "boost-holders":
            result = bot.boost_holders(args.token_address, **(args.extra or {}))
        elif args.command == "withdraw":
            result = bot.withdraw(args.token_address, **(args.extra or {}))
        elif args.command == "token-info":
            result = bot.token_info(args.token_address)
        elif args.command == "internal-wallets":
            result = bot.internal_wallets(args.token_address)
        elif args.command == "list":
            result = bot.list_launched_tokens()
        elif args.command == "tokens":
            result = bot.get_tokens_metadata(args.addresses if args.addresses else None)
        else:
            parser.print_help()
            return 1

        _print_json(result)
        return 0

    except TokenLauncherError as e:
        print(f"Error: {e}", file=sys.stderr)
        if e.response and hasattr(e.response, "text"):
            print(e.response.text, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
