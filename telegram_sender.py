# telegram_sender.py — FINAL VERSION (Heartbeat + fire{mint} format)
from telegram import Bot
from telegram.error import TelegramError
import asyncio
class TelegramSender:
    def __init__(self, bot_token: str, channel_id: str):
        self.bot = Bot(token=bot_token)
        self.channel_id = int(channel_id)
    async def send_token(self, contract: str):
        # This is the format (UX-SolSniper loves this)
        message = f"🔥 {contract}"
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                disable_web_page_preview=True
            )
            print(f"SENT → 🔥{message}")
        except TelegramError as e:
            print(f"Telegram ERROR: {e}")