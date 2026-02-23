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


def _parse_rate_limit_info(error: TokenLauncherError) -> dict | None:
    """Extract retryAfter (seconds) from rate limit error response."""
    if not error.response or not hasattr(error.response, "text"):
        return None
    try:
        data = json.loads(error.response.text)
        if data.get("error") == "Rate limit exceeded" and "retryAfter" in data:
            return {"retryAfter": data["retryAfter"], "message": data.get("message", "")}
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def _format_retry_after(seconds: int) -> str:
    """Format retryAfter seconds as human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def _extract_wallet_addresses(resp: dict) -> list[str]:
    """Extract wallet addresses from internal-wallets API response."""
    if isinstance(resp, list):
        items = resp
    elif isinstance(resp, dict):
        items = resp.get("wallets") or resp.get("addresses") or resp.get("data") or []
    else:
        return []
    addresses = []
    for item in items:
        if isinstance(item, str) and item.startswith("0x"):
            addresses.append(item)
        elif isinstance(item, dict):
            addr = item.get("address") or item.get("wallet") or item.get("walletAddress")
            if addr:
                addresses.append(addr)
    return addresses


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
    withdraw_parser.add_argument(
        "--from-address",
        "-f",
        help="Internal wallet address (auto-fetched if omitted and exactly one exists)",
    )
    withdraw_parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Withdraw from all internal wallets",
    )
    withdraw_parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=None,
        metavar="N",
        help="Max withdrawals per run (API limit: 10/day). Stops on rate limit.",
    )
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
            extra = args.extra or {}
            wallets_resp = bot.internal_wallets(args.token_address)
            addresses = _extract_wallet_addresses(wallets_resp)

            if not addresses:
                print(
                    "Error: No internal wallets found. Use internal-wallets to check.",
                    file=sys.stderr,
                )
                return 1

            if getattr(args, "all", False):
                # Withdraw from all wallets (respect limit, stop on rate limit)
                results = []
                limit = getattr(args, "limit", None)
                rate_limited = False
                rate_limit_info = None
                for i, addr in enumerate(addresses):
                    if limit is not None and i >= limit:
                        break
                    extra["fromAddress"] = addr
                    try:
                        r = bot.withdraw(args.token_address, **extra)
                        results.append({"address": addr, "success": True, "result": r})
                    except TokenLauncherError as e:
                        rl = _parse_rate_limit_info(e)
                        if rl:
                            rate_limited = True
                            rate_limit_info = rl
                            results.append({"address": addr, "success": False, "error": str(e)})
                            break
                        results.append({"address": addr, "success": False, "error": str(e)})
                result = {
                    "withdrawals": results,
                    "summary": {
                        "success": sum(1 for r in results if r.get("success")),
                        "failed": sum(1 for r in results if not r.get("success")),
                        "total_wallets": len(addresses),
                    },
                }
                if rate_limit_info:
                    result["rateLimit"] = {
                        "retryAfterSeconds": rate_limit_info["retryAfter"],
                        "retryAfter": _format_retry_after(rate_limit_info["retryAfter"]),
                        "message": rate_limit_info["message"],
                    }
            else:
                from_address = args.from_address
                if not from_address:
                    if len(addresses) == 1:
                        from_address = addresses[0]
                    else:
                        print(
                            f"Error: Multiple internal wallets ({len(addresses)}). "
                            "Use --from-address/-f or --all",
                            file=sys.stderr,
                        )
                        for a in addresses:
                            print(f"  {a}", file=sys.stderr)
                        return 1
                extra["fromAddress"] = from_address
                result = bot.withdraw(args.token_address, **extra)
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
