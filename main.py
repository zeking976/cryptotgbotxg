import os
import asyncio
from dotenv import load_dotenv
from token_fetcher import TokenFetcher
from telegram_sender import TelegramSender
load_dotenv('t.env')
BOT_TOKEN       = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_CHANNEL  = os.getenv("TARGET_CHANNEL_ID")
if not BOT_TOKEN or not TARGET_CHANNEL:
    raise SystemExit("Missing BOT_TOKEN or TARGET_CHANNEL_ID in t.env")
sender  = TelegramSender(BOT_TOKEN, TARGET_CHANNEL)
fetcher = TokenFetcher()
async def main():
    print("Bot STARTED — Reading source channel → Filtering → Sending via Bot Token")
    print("Signals will be sent as: 🔥{contract}")
    print(f"Target channel: {TARGET_CHANNEL}")
    task = asyncio.create_task(fetcher.start())
    try:
        await task
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        fetcher.client.disconnect()   # ← proper Telethon shutdown
        await asyncio.sleep(1)
        print("Bot stopped cleanly.")
if __name__ == "__main__":