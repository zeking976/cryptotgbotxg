# CryptoTGBotXG

Telegram bot for new Solana tokens from Pump.fun & Raydium.

## Setup
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill values.
3. Add bot to channel as admin.
4. `python main.py`

## Filters
- MCap: $10k - $1M
- Liq/MCap Ratio: >10
- Rug: Top holder <50% supply

## APIs Used
- Moralis: Pump.fun new tokens
- Dexscreener: Raydium new pairs
- Jupiter: MCap/Liq
- Solana RPC: Holder check
