"""Token Launcher API client for the public API at api.tokenlauncher.com."""

from __future__ import annotations

import os
from typing import Any

import httpx

BASE_URL = "https://api.tokenlauncher.com/public"


class TokenLauncherError(Exception):
    """Raised when an API request fails."""

    def __init__(self, message: str, status_code: int | None = None, response: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class TokenLauncherClient:
    """Client for the Token Launcher Public API."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = BASE_URL,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.environ.get("TOKEN_LAUNCHER_API_KEY")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _headers(self, require_auth: bool = False) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        elif require_auth:
            raise TokenLauncherError(
                "API key required. Set TOKEN_LAUNCHER_API_KEY or pass api_key to the client."
            )
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
        require_auth: bool = False,
    ) -> dict:
        url = f"{self.base_url}{path}"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.request(
                method,
                url,
                json=json,
                params=params,
                headers=self._headers(require_auth=require_auth),
            )
        if response.status_code >= 400:
            raise TokenLauncherError(
                f"API error: {response.text}",
                status_code=response.status_code,
                response=response,
            )
        return response.json() if response.content else {}

    # --- Write operations (require API key) ---

    def launch_token(
        self,
        name: str,
        symbol: str,
        **kwargs: Any,
    ) -> dict:
        """Launch a new token with liquidity pool."""
        payload = {"name": name, "symbol": symbol, **kwargs}
        return self._request("POST", "/launchToken", json=payload, require_auth=True)

    def boost_price(self, token_address: str, **kwargs: Any) -> dict:
        """Boost token price."""
        payload = {"tokenAddress": token_address, **kwargs}
        return self._request("POST", "/boostPrice", json=payload, require_auth=True)

    def boost_volume(self, token_address: str, **kwargs: Any) -> dict:
        """Generate trading volume for a token."""
        payload = {"tokenAddress": token_address, **kwargs}
        return self._request("POST", "/boostVolume", json=payload, require_auth=True)

    def boost_holders(self, token_address: str, **kwargs: Any) -> dict:
        """Increase holder count for a token."""
        payload = {"tokenAddress": token_address, **kwargs}
        return self._request("POST", "/boostHolders", json=payload, require_auth=True)

    def withdraw(self, token_address: str, **kwargs: Any) -> dict:
        """Withdraw tokens from internal wallet."""
        payload = {"tokenAddress": token_address, **kwargs}
        return self._request("POST", "/withdraw", json=payload, require_auth=True)

    # --- Read operations (no auth required for public info) ---

    def get_internal_wallets(self, token_address: str) -> dict:
        """Get internal wallets holding a token."""
        path = f"/internalWallets/{token_address}"
        return self._request("GET", path)

    def get_public_token_info(self, token_address: str) -> dict:
        """Get token info for any token."""
        path = f"/public-token-info/{token_address}"
        return self._request("GET", path)

    def get_tokens(self, addresses: list[str] | None = None) -> dict:
        """Get full token metadata by addresses."""
        params = {}
        if addresses:
            params["addresses"] = addresses
        return self._request("GET", "/tokens", params=params or None)

    def list_tokens(self) -> dict:
        """List all launched token addresses."""
        return self._request("GET", "/tokens/list")
