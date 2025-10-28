import os
import time
import asyncio
from dotenv import load_dotenv
from token_fetcher import TokenFetcher
from filters import passes_filters
from telegram_sender import TelegramSender

load_dotenv('t.env')  # Your renamed file

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
MORALIS_KEY = os.getenv("MORALIS_API_KEY")
RPC = os.getenv("RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")

if not all([BOT_TOKEN, CHANNEL_ID, MORALIS_KEY]):
    raise ValueError(f"Missing env: Bot={bool(BOT_TOKEN)}, Channel={bool(CHANNEL_ID)}, Moralis={bool(MORALIS_KEY)}")

print("🚀 Bot starting...")
sender = TelegramSender(BOT_TOKEN, CHANNEL_ID)
fetcher = TokenFetcher(MORALIS_KEY)
seen_mints = set()

async def main_loop():
    while True:
        all_tokens = fetcher.get_new_pump_tokens() + fetcher.get_new_ray_tokens()
        print(f"Processing {len(all_tokens)} new tokens...")
        for t in all_tokens:
            mint = t["mint"]
            if mint not in seen_mints and passes_filters(t):
                print(f"✅ Token {mint} passed filters—sending!")
                await sender.send_token(mint)
                seen_mints.add(mint)
            else:
                print(f"⏭️ Skipped {mint}")
        print("⏳ Sleeping 10s...")
        time.sleep(10)

if __name__ == "__main__":
    asyncio.run(main_loop())