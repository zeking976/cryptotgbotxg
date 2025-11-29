# main.py
import os
import asyncio
import time
import requests
from dotenv import load_dotenv
from token_fetcher import TokenFetcher
from filters import passes_filters
from telegram_sender import TelegramSender

load_dotenv('t.env')

BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID  = os.getenv("TARGET_CHANNEL_ID")
RPC         = os.getenv("RPC_ENDPOINT", "https://api.mainnet-beta.solana.com")

if not BOT_TOKEN or not CHANNEL_ID:
    raise SystemExit("Missing BOT_TOKEN or CHANNEL_ID in t.env")

sender   = TelegramSender(BOT_TOKEN, CHANNEL_ID)
fetcher  = TokenFetcher()
seen     = set()
watching = {}  # mint → data

async def get_price(mint: str) -> float:
    try:
        r = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{mint}", timeout=8)
        pair = r.json()["pairs"][0]
        return float(pair["priceUsd"])
    except:
        return 0.0

async def main_loop():
    while True:
        try:
            new = fetcher.get_new_tokens()
            trend = fetcher.get_trending_tokens()
            candidates = new + trend
            now = time.time()

            # Add fresh tokens to watchlist
            for t in candidates:
                mint = t["mint"]
                if mint in seen or mint in watching:
                    continue
                price = await get_price(mint)
                if price > 0:
                    watching[mint] = {
                        "token": t,
                        "launch_price": price,
                        "first_seen": now
                    }
                    print(f"Watching → {mint[:8]}... | Launch ${price:.6f}")

            # Monitor watched tokens
            remove = []
            for mint, info in watching.items():
                t = info["token"]
                age_min = (now - info["first_seen"]) / 60
                price = await get_price(mint)
                if price <= 0:
                    continue

                change = (price / info["launch_price"] - 1) * 100

                # Golden window: 3–25 min old + already +35%
                if 3 <= age_min <= 25 and change >= 35:
                    if passes_filters(t, RPC):
                        await sender.send_token(mint)
                        print(f"SNIPED +{change:.1f}% ({age_min:.0f}min) → {mint}")
                        seen.add(mint)
                        remove.append(mint)

                # Late but insane pump
                elif age_min > 25 and change >= 80:
                    if passes_filters(t, RPC):
                        await sender.send_token(mint)
                        print(f"LATE PUMP +{change:.1f}% → {mint}")
                        seen.add(mint)
                        remove.append(mint)

            for m in remove:
                watching.pop(m, None)

            print(f"Watching: {len(watching)} | Sniped today: {len(seen)}")
        except Exception as e:
            print(f"Loop error: {e}")

        await asyncio.sleep(18)  # Check every 18 seconds

if __name__ == "__main__":
    asyncio.run(main_loop())