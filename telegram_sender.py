# telegram_sender.py
from telegram import Bot
from telegram.error import TelegramError
import asyncio

class TelegramSender:
    def __init__(self, bot_token: str, channel_id: str):
        self.bot = Bot(token=bot_token)
        self.channel_id = channel_id

    async def send_token(self, contract: str):
        message = f"🔥{contract}"
        try:
            await self.bot.send_message(chat_id=self.channel_id, text=message)
            print(f"Sent: {message}")
        except TelegramError as e:
            print(f"Telegram ERROR: {e}")