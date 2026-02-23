"""Token Launcher bot - high-level interface for token operations."""

from __future__ import annotations

import json
from typing import Any

from .client import TokenLauncherClient, TokenLauncherError


class TokenLauncherBot:
    """Bot for launching and managing tokens on Base chain via Token Launcher API."""

    def __init__(self, api_key: str | None = None, **client_kwargs: Any):
        self.client = TokenLauncherClient(api_key=api_key, **client_kwargs)

    def launch(self, name: str, symbol: str, **kwargs: Any) -> dict:
        """Launch a new token with liquidity pool."""
        return self.client.launch_token(name, symbol, **kwargs)

    def boost_price(self, token_address: str, **kwargs: Any) -> dict:
        """Boost token price."""
        return self.client.boost_price(token_address, **kwargs)

    def boost_volume(self, token_address: str, **kwargs: Any) -> dict:
        """Generate trading volume."""
        return self.client.boost_volume(token_address, **kwargs)

    def boost_holders(self, token_address: str, **kwargs: Any) -> dict:
        """Increase holder count."""
        return self.client.boost_holders(token_address, **kwargs)

    def withdraw(self, token_address: str, **kwargs: Any) -> dict:
        """Withdraw tokens from internal wallet."""
        return self.client.withdraw(token_address, **kwargs)

    def token_info(self, token_address: str) -> dict:
        """Get public token info."""
        return self.client.get_public_token_info(token_address)

    def internal_wallets(self, token_address: str) -> dict:
        """Get internal wallets holding a token."""
        return self.client.get_internal_wallets(token_address)

    def list_launched_tokens(self) -> dict:
        """List all launched token addresses."""
        return self.client.list_tokens()

    def get_tokens_metadata(self, addresses: list[str] | None = None) -> dict:
        """Get full token metadata by addresses."""
        return self.client.get_tokens(addresses)
