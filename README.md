# Token Launcher Bot

A Python bot for the [Token Launcher Public API](https://api.tokenlauncher.com/public/docs/) — launch and manage tokens on Base chain.

## Setup

1. **Install dependencies**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure API key**

   Get your API key from [Account Settings](https://tokenlauncher.com/account). Then:

   ```bash
   cp .env.example .env
   # Edit .env and add your TOKEN_LAUNCHER_API_KEY
   ```

   Or set the environment variable:

   ```bash
   export TOKEN_LAUNCHER_API_KEY=your_api_key_here
   ```

## CLI Usage

### Launch a token

```bash
python main.py launch "My Token" "MTK"
```

With optional metadata:

```bash
python main.py launch "My Token" "MTK" \
  --description "A great token" \
  --website "https://mytoken.com" \
  --twitter "https://twitter.com/mytoken" \
  --telegram "https://t.me/mytoken"
```

### Boost operations (require API key)

```bash
# Boost token price
python main.py boost-price 0xYourTokenAddress

# Generate trading volume
python main.py boost-volume 0xYourTokenAddress

# Increase holder count
python main.py boost-holders 0xYourTokenAddress
```

### Withdraw

Requires `--from-address` (the internal wallet to withdraw from). Use `internal-wallets` to list addresses:

```bash
python main.py internal-wallets 0xYourTokenAddress
python main.py withdraw 0xYourTokenAddress --from-address 0xInternalWalletAddress
```

### Read-only queries

```bash
# Get public token info
python main.py token-info 0xAnyTokenAddress

# Get internal wallets holding a token
python main.py internal-wallets 0xTokenAddress

# List all launched token addresses
python main.py list

# Get full token metadata by addresses
python main.py tokens 0xAddr1 0xAddr2
```

## Python API

```python
from tokenlauncher import TokenLauncherBot

bot = TokenLauncherBot(api_key="your_key")  # or from env

# Launch
result = bot.launch("My Token", "MTK")

# Boost
bot.boost_price("0x...")
bot.boost_volume("0x...")
bot.boost_holders("0x...")

# Withdraw
bot.withdraw("0x...")

# Query
info = bot.token_info("0x...")
wallets = bot.internal_wallets("0x...")
tokens = bot.list_launched_tokens()
metadata = bot.get_tokens_metadata(["0x...", "0x..."])
```

## API Reference

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/launchToken` | POST | Yes | Launch token with liquidity pool |
| `/boostPrice` | POST | Yes | Boost token price |
| `/boostVolume` | POST | Yes | Generate trading volume |
| `/boostHolders` | POST | Yes | Increase holder count |
| `/withdraw` | POST | Yes | Withdraw from internal wallet |
| `/internalWallets/{tokenAddress}` | GET | Yes | Internal wallets holding token |
| `/public-token-info/{tokenAddress}` | GET | Yes | Public token info |
| `/tokens` | GET | Yes | Token metadata by addresses |
| `/tokens/list` | GET | Yes | List launched token addresses |

## Links

- [API Docs](https://api.tokenlauncher.com/public/docs/)
- [Account / API Key](https://tokenlauncher.com/account)
- [Volume Booster](https://tokenlauncher.com/volume-booster)
