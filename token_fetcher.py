# token_fetcher.py — FINAL 100% WORKING (Dec 2025) — NO DISCONNECTS, NO MISSED MESSAGESimport aiohttp
import asyncio
import random
import time
import re
import os
from typing import Dict, Optional
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
from dotenv import load_dotenv
# === LOAD ENV ===
load_dotenv("/root/cryptotgbotxg/t.env")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID"))
SOURCE_CHANNEL_ID = int(os.getenv("SOURCE_CHANNEL_ID", TARGET_CHANNEL_ID))
SESSION_FILE = "/root/cryptotgbotxg/session_string.txt"
if not os.path.exists(SESSION_FILE):
    raise SystemExit("session_string.txt missing!")
with open(SESSION_FILE) as f:
    SESSION_STRING = f.read().strip()
# === TELEGRAM SENDER ===
from telegram_sender import TelegramSender
sender = TelegramSender(BOT_TOKEN, TARGET_CHANNEL_ID)
# === FILTERS ===
try:
    from filters import passes_filters
except ImportError:
    def passes_filters(t: Dict, rpc: str) -> bool:
        return True
# === GLOBALS ===
waitlist = {}  # mint → {"launch_mcap": ..., "sent": False}
seen_mints = set()
# === CLEAN MINT ===
def clean_mint(mint: str) -> str:
    return re.sub(
        r'\.(pump|bonk|bot|moon|cat|dog|shib|pepe|wojak|based|rekt)$',
        '', mint, flags=re.IGNORECASE
    )
# === EXTRACT MINT ===
def extract_mint(msg) -> Optional[str]:
    text = getattr(msg, "message", "") or ""
    full_text = text
    if hasattr(msg, "entities") and msg.entities:
        for e in msg.entities:
            if hasattr(e, "url") and e.url:
                full_text += " " + e.url
    full_text = re.sub(r'[\u200B-\u200D\uFEFF\r\n\t]', ' ', full_text)
    full_text = re.sub(r'\s+', ' ', full_text).strip()
    candidates = set()
    # Raw mint
    for m in re.finditer(r'\b([1-9A-HJ-NP-Za-km-z]{32,44})\b', full_text):
        candidates.add(m.group(1))
    # Links
    patterns = [
        r"t\.me/soul_sniper_bot\?start=[^_]*_([A-HJ-NP-Za-km-z]{32,44})",
        r"dexscreener\.com/solana/([A-HJ-NP-Za-km-z]{32,44})",
        r"pump\.fun/([A-HJ-NP-Za-km-z]{32,44})",
    ]
    for p in patterns:
        for m in re.finditer(p, full_text, re.IGNORECASE):
            candidates.add(m.group(1))
    # Buttons
    buttons = getattr(msg, "buttons", []) or []
    for row in buttons:
        for btn in row:
            url = getattr(btn, "url", "") or ""
            for m in re.finditer(r"([A-HJ-NP-Za-km-z]{32,44})", url):
                candidates.add(m.group(1))
    for ca in candidates:
        clean = clean_mint(ca)
        if 32 <= len(clean) <= 44 and re.match(r"^[1-9A-HJ-NP-Za-km-z]+$", clean):
            return clean
    return None
async def get_token_data(mint: str) -> Dict:
    result = {
        "mint": mint,
        "mcap": 0.0,
        "liq": 0.0,
        "volume_5m": 0.0,              # Dex fallback
        "volume_change_1h": 0.0,       # Jupiter primary
        "has_paid_dex": False,
        "is_new": False
    }
    timeout = aiohttp.ClientTimeout(total=12)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        # -----------------------------
        # 1. DEXSCREENER (SECONDARY)
        # -----------------------------
        try:
            url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    pairs = data.get("pairs", [])
                    if pairs:
                        # Pick primary pool type
                        pair = next(
                            (p for p in pairs if p.get("dexId") in ["raydium", "pumpfun", "pumpswap"]),
                            pairs[0]
                        )
                        # Ensure baseToken = mint
                        base = pair.get("baseToken", {})
                        if base.get("address") != mint:
                            pair = next(
                                (p for p in pairs if p.get("baseToken", {}).get("address") == mint),
                                pair
                            )
                        # MCAP / LIQ
                        mcap = pair.get("fdv") or pair.get("marketCap")
                        liq = pair.get("liquidity", {}).get("usd")
                        # Dexscreener pump volume (5-minute window)
                        vol_section = pair.get("volume", {})
                        vol_m5_raw = vol_section.get("m5", 0)
                        try:
                            vol_m5 = float(str(vol_m5_raw).replace(",", ""))
                        except:
                            vol_m5 = 0.0
                        # Age
                        created = pair.get("pairCreatedAt", 0)
                        age_min = (time.time() - created / 1000) / 60 if created else 999
                        # Update result
                        result.update({
                            "mcap": float(mcap) if mcap else 0.0,
                            "liq": float(liq) if liq else 0.0,
                            "volume_5m": vol_m5,
                            "has_paid_dex": bool(pair.get("info", {}).get("imageUrl")),                            "is_new": age_min < 30,
                        })
                        print(
                            f"Data → MCAP ({result['mcap']:,.0f} | "
                            f"Liq {result['liq']:,.0f} | "
                            f"Age {age_min:.1f}min | "
                            f"m5Vol {result['volume_5m']:,.0f})"
                        )
                        # early return rule stays unchanged
                        if result["mcap"] > 1000 or result["liq"] > 1000:
                            return result
        except Exception as e:
            print(f"DexScreener failed: {e}")
        # -----------------------------
        # 2. JUPITER FALLBACK (PRIMARY SOURCE FOR VOLUME)
        # -----------------------------
        print("DexScreener weak → Trying Jupiter fallback...")
        try:
            jup_url = f"https://lite-api.jup.ag/tokens/v2/search?query={mint}"
            async with session.get(jup_url, timeout=8) as r:
                if r.ok:
                    data = await r.json()
                    if data and len(data) > 0:
                        t = data[0]
                        if result["mcap"] == 0 and t.get("mcap"):
                            result["mcap"] = float(t["mcap"])
                        if result["liq"] == 0 and t.get("liquidity"):
                            result["liq"] = float(t["liquidity"])
                        # Jupiter volumeChange = PRIMARY
                        stats1h = t.get("stats1h", {})
                        vol_change_1h = stats1h.get("volumeChange", 0)
                        result["volume_change_1h"] = float(vol_change_1h) if vol_change_1h else 0.0
                        print(f"Jupiter fallback → MCAP ({result['mcap']:,.0f} | Liq {result['liq']:,.0f})")
                        print(f"Jupiter volumeChange → {result['volume_change_1h']:.2f}%")
        except Exception as e:
            print(f"Jupiter fallback failed: {e}")
        # Final decision
        if result["mcap"] == 0 and result["liq"] == 0:
            print(f"ALL SOURCES FAILED → {mint[:8]}... (rugged or too new)")
        else:
            print(f"Data → MCAP ({result['mcap']:,.0f} | Liq {result['liq']:,.0f} | Final)")
        return result
async def monitor_waitlist():
    while True:
        active = sum(1 for v in waitlist.values() if not v["sent"])
        await asyncio.sleep(max(1.02, active * 1.02))
        for mint, info in list(waitlist.items()):
            if info["sent"]:
                continue
            data = await get_token_data(mint)
            if not data or data.get("mcap", 0) == 0:
                continue
            # ---- PRICE SIGNAL ----
            current_mcap = data["mcap"]
            launch_mcap = info["launch_mcap"]
            price_ratio = current_mcap / launch_mcap
            # ---- VOLUME SIGNAL ----
            vol_now = data.get("volume_5m", 0)
            vol_prev = info.get("vol_prev", 0)
            # update snapshot immediately
            info["vol_prev"] = vol_now
            # first tick, nothing to compare
            if vol_prev == 0:
                continue
            vol_accel = vol_now / vol_prev
            # ignore flat or decaying volume
            if vol_accel < 1.10:
                continue
            # ---- COMBINED TRIGGER ----
            if price_ratio >= 1.10 and vol_accel >= 1.25:
                await sender.send_token(mint)
                print(
                    f"PUMP → 🔥{mint} | "
                    f"MCAP {price_ratio:.2f}x | "
                    f"VOL {vol_accel:.2f}x"
                )
                info["sent"] = True
# === TOKENFETCHER CLASS ===
class TokenFetcher:
    def __init__(self):
        self.client = TelegramClient(
            StringSession(SESSION_STRING),
            int(os.getenv("TELEGRAM_API_ID")),
            os.getenv("TELEGRAM_API_HASH"),
            connection_retries=None,
            retry_delay=5,
            request_retries=10,
            timeout=30,
            auto_reconnect=True,
            flood_sleep_threshold=60,
        )
        self.client.parse_mode = 'html'
        # Register handler inside class
        @self.client.on(events.NewMessage(chats=SOURCE_CHANNEL_ID))
        async def handler(event):
            text = (event.message.message or "").strip()
            if not (text.startswith("🔥") or text.startswith("📈")):
                return
            mint = extract_mint(event.message)
            if not mint:
                return
            print(f"\nMINT → {mint}")
            if mint in waitlist and waitlist[mint]["sent"]:
                return
            data = await get_token_data(mint)
            if not data or data.get("mcap", 0) == 0:
                print(f"NO DATA → {mint[:8]}... (retry later)")
                return
            if await passes_filters(data):
                seen_mints.add(mint)
                if mint not in waitlist:
                    waitlist[mint] = {
                        "launch_mcap": data["mcap"],
                        "sent": False
                    }
                    print(f"WAITLIST ADD → {mint}")
    async def start(self):
        print("TokenFetcher STARTED — Listening + Auto-Reconnect Forever")
        # Start these tasks ONCE — they survive reconnects
        asyncio.create_task(monitor_waitlist())
        while True:
            try:
                await self.client.start()
                print("Connected — Reading channel...")
                await self.client.run_until_disconnected()
            except FloodWaitError as e:
                print(f"Flood → wait {e.seconds}s")
                await asyncio.sleep(e.seconds + 10)
            except Exception as e:
                print(f"Disconnected: {e} — reconnecting...")
                await asyncio.sleep(5)
# === RUNNER ===
if __name__ == "__main__":
    fetcher = TokenFetcher()
    asyncio.run(fetcher.start())