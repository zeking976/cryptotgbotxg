import os
import time
from dotenv import load_dotenv
from token_fetcher import TokenFetcher
from filters import passes_filters
from telegram_sender import TelegramSender

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")
MORALIS_KEY = os.getenv("MORALIS_API_KEY")
RPC = os.getenv("RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")

if not all([BOT_TOKEN, CHANNEL_ID, MORALIS_KEY]):
    raise ValueError("Missing env vars")

sender = TelegramSender(BOT_TOKEN, CHANNEL_ID)
fetcher = TokenFetcher(MORALIS_KEY)

seen_mints = set()

async def main():
    while True:
        # Fetch new from Pump.fun
        pump_tokens = fetcher.get_new_pump_tokens()
        for t in pump_tokens:
            mint = t["mint"]
            if mint not in seen_mints and passes_filters(mint, RPC):
                await sender.send_token(mint)
                seen_mints.add(mint)

        # Fetch new from Raydium
        ray_tokens = fetcher.get_new_ray_tokens()
        for t in ray_tokens:
            mint = t["mint"]
            if mint not in seen_mints and passes_filters(mint, RPC):
                await sender.send_token(mint)
                seen_mints.add(mint)

        time.sleep(10)  # Poll every 10s

if __name__ == "__main__":
    asyncio.run(main())