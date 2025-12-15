---

🚀 CryptoTGBotXG

Telegram bot for early Solana token discovery and momentum-based entries from Pump.fun & Raydium.


---

⚙️ Setup

pip install -r requirements.txt

1. Copy .env.example → t.env (IMPORTANT)


2. Fill all required API keys


3. Add the bot to your Telegram channel as admin


4. Run:



python main.py


---

🧠 Strategy (Updated)

Tokens are first added to a wait-list

Bot monitors live MCAP + short-term volume

Entry signal only fires on real momentum, not hype


📈 Entry Trigger

MCAP increase ≥ +6% from launch

5-minute volume acceleration ≥ 1.20×

Dynamic polling based on active wait-list size



---

🔍 Filters (Current)

MCAP: $19k – $1,000,000

Liquidity: ≥ $10,000

MCAP / LIQ Ratio: ≤ 6.1

Volume: Strong 5-minute activity

Rug Check: Holder & mint safety checks



---

🔗 APIs Used

Dexscreener – volume & price data

Jupiter – liquidity & routing

Solana RPC – on-chain validation



---

⚡ Goal

Catch early pumps with confirmation, avoid dead tokens, and enter before the crowd.


---