import os, time, asyncio
from dotenv import load_dotenv
from token_fetcher import TokenFetcher
from filters import passes_filters
from telegram_sender import TelegramSender

load_dotenv('t.env')

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID  = os.getenv("TARGET_CHANNEL_ID")
BITQUERY_KEY = os.getenv("BITQUERY_API_KEY")
RPC         = os.getenv("RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")

if not all([BOT_TOKEN, CHANNEL_ID, BITQUERY_KEY]):
    raise SystemExit("Missing env vars")

print("🚀 Bitquery Pump Bot starting...")
sender  = TelegramSender(BOT_TOKEN, CHANNEL_ID)
fetcher = TokenFetcher(BITQUERY_KEY)
seen    = set()

async def loop():
    while True:
        # New + Trending
        new_tokens = fetcher.get_new_pump_tokens()
        trend_tokens = fetcher.get_trending_pump_tokens()
        all_tokens = new_tokens + trend_tokens
        print(f"Processing {len(all_tokens)} Pump candidates (new+trend)...")
        for t in all_tokens:
            mint = t["mint"]
            if mint in seen: continue
            if passes_filters(t, RPC):
                await sender.send_token(mint)
                seen.add(mint)
            else:
                print(f"⏭️ Skipped {mint}")
        print("⏳ Sleeping 12s...")
        await asyncio.sleep(12)

if __name__ == "__main__":
    asyncio.run(loop())