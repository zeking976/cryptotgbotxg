# filters.py — SAME HIGH WIN-RATE FILTERS (works for all Solana tokens)
import requests
import time
from typing import Dict
import aiohttp
import asyncio
import json
_last_jup_call = 0
_jup_cooldown = 1.05  # 500ms spacing
async def is_rug_filter(mint: str) -> bool:
    global _last_jup_call
    elapsed = time.time() - _last_jup_call
    if elapsed < _jup_cooldown:
        await asyncio.sleep(_jup_cooldown - elapsed)
    _last_jup_call = time.time()
    url = f"https://lite-api.jup.ag/tokens/v2/search?query={mint}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as r:
                if r.status != 200:
                    print(f"Jupiter audit fetch failed {r.status} → allowing")
                    return True  # don’t block on bad network
                data = await r.json()
                if not data or len(data) == 0:
                    print("Jupiter audit → empty result → allowing")
                    return True
                token = data[0]
                audit = token.get("audit", {})
                if not audit:
                    print("Audit field missing → cannot verify → allowing")
                    return True
                top_pct = audit.get("topHoldersPercentage", None)
                if top_pct is None:
                    print("Audit topHoldersPercentage missing → allowing")
                    return True
                print(f"Audit top holders % = {top_pct:.2f}%")
                # ===== RUG LOGIC (based only on Jupiter audit) =====
                if top_pct >= 70:
                    print(f"RUG → {top_pct:.2f}% top holder → BLOCKED")
                    return False
                if top_pct >= 60:
                    print(f"Warning → High risk: {top_pct:.2f}% top holder (allowed)")
                return True
    except Exception as e:
        print(f"Audit check failed → allowing: {e}")
        return True
async def passes_filters(t: Dict) -> bool:
    mint = t["mint"]
    mcap = t.get("mcap", 0)
    liq = t.get("liq", 0)
    # =============================
    # VOLUME FILTER (NEW + CORRECT)
    # =============================
    # Dexscreener → strong short-term signal
    vol_5m = (
        t.get("volume_5m")
        or t.get("m5_volume")
        or t.get("volume", {}).get("m5")
        or 0
    )
    # Jupiter → directional momentum (positive or negative)
    vol_change_1h = (
        t.get("volume_change_1h")
        or t.get("volume", {}).get("h1_change")
        or 0
    )
    # 1. Require early pump emergence
    if vol_5m < 15000:
        print(f"LOW 5M VOLUME → {vol_5m}")
        return False
    # 2. Require positive 1-hour momentum
    if vol_change_1h < -0.20:
        print(f"NEGATIVE 1H VOLUME CHANGE → {vol_change_1h}")
        return False
    # =============================
    # DO NOT TOUCH ANYTHING ELSE
    # =============================
    # MCAP RANGE
    if not (19_000 <= mcap <= 400_000):
        print(f"MCAP OUT → ${mcap:,.0f}")
        return False
    # MCAP / LIQ RATIO
    ratio = mcap / liq if liq > 0 else 999
    if ratio > 8:
        print(f"RATIO TOO HIGH → {ratio:.1f}x")
        return False
    # MINIMUM LIQUIDITY
    if liq < 10_000:
        print(f"LIQ TOO LOW → ${liq:,.0f}")
        return False
    return True