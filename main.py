import os, time, asyncio
from dotenv import load_dotenv
from token_fetcher import TokenFetcher
from filters import passes_filters
from telegram_sender import TelegramSender

load_dotenv('t.env')

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID  = os.getenv("TARGET_CHANNEL_ID")
RPC         = os.getenv("RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")

if not all([BOT_TOKEN, CHANNEL_ID]):
    raise SystemExit("Missing env vars")

print("DexScreener Pump Bot starting🚀...")
sender  = TelegramSender(BOT_TOKEN, CHANNEL_ID)
fetcher = TokenFetcher()
seen    = set()

async def loop():
    while True:
        new_tokens = fetcher.get_new_tokens()
        trend_tokens = fetcher.get_trending_tokens()
        all_tokens = new_tokens + trend_tokens

        print(f"Processing {len(all_tokens)} candidates📊...")
        for t in all_tokens:
            mint = t["mint"]
            if mint in seen: continue
            if passes_filters(t, RPC):
                await sender.send_token(mint)
                seen.add(mint)
            else:
                print(f"🔃Skipped {mint}")
        print("Sleeping 12s...")
        await asyncio.sleep(12)

if __name__ == "__main__":
    asyncio.run(loop())