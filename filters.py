# filters.py — SAME HIGH WIN-RATE FILTERS (works for all Solana tokens)
import requests
import time
from typing import Dict

def is_rug_filter(mint: str, rpc: str) -> bool:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenLargestAccounts", "params": [mint]}
    try:
        r = requests.post(rpc.rstrip("/"), json=payload, timeout=6)
        r.raise_for_status()
        top = r.json()["result"]["value"][0]["uiAmount"]
        if top > 0.5 * 1_000_000_000:
            print(f"RUG RISK → {mint}")
            return False
        return True
    except:
        return True

def passes_filters(t: Dict, rpc: str) -> bool:
    mint = t["mint"]
    mcap = t["mcap"]
    liq = t["liq"]
    vol = t.get("volume_usd", 0)

    # Relaxed MCAP for normal tokens (some gems launch at $20k)
    if not (20000 < mcap < 800000):
        print(f"MCAP out: ${mcap:,.0f}")
        return False

    if liq == 0 or mcap / liq <= 10:
        print(f"Low ratio: {mcap/liq:.1f}x")
        return False

    if not t.get("is_new", False):
        if not t.get("has_paid_dex", False):
            print(f"No paid Dex (trending): {mint}")
            return False

    if not is_rug_filter(mint, rpc):
        return False

    print(f"PASSED: {mint} | \( {mcap:,.0f} | {mcap/liq:.1f}x | Vol \){vol:,.0f}")
    return True