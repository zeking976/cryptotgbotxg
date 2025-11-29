# filters.py
import requests
import time
from typing import Dict

def is_rug_filter(mint: str, rpc: str) -> bool:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenLargestAccounts", "params": [mint]}
    try:
        r = requests.post(rpc.rstrip("/"), json=payload, timeout=6)
        r.raise_for_status()
        top = r.json()["result"]["value"][0]["uiAmount"]
        if top > 0.5 * 1_000_000_000:  # >50%
            print(f"RUG RISK → {mint}")
            return False
        return True
    except:
        return True  # fail-open

def passes_filters(t: Dict, rpc: str) -> bool:
    mint = t["mint"]
    mcap = t["mcap"]
    liq = t["liq"]
    vol = t.get("volume_usd", 0)
    age_min = (time.time() - t.get("created_at", time.time())) / 60

    # Hard filters (your choice)
    if not (25000 < mcap < 700000):
        print(f"MCAP out: ${mcap:,.0f}")
        return False
    if liq == 0 or mcap / liq <= 10:
        print(f"Low ratio: {mcap/liq:.1f}x")
        return False

    # Paid Dex only for trending
    if not t.get("is_new", False):
        if not t.get("has_paid_dex", False):
            print(f"No paid Dex (trending): {mint}")
            return False
    else:
        print(f"New token — paid Dex optional")

    if not is_rug_filter(mint, rpc):
        return False

    print(f"PASSED: {mint} | \( {mcap:,.0f} | {mcap/liq:.1f}x | Vol \){vol:,.0f}")
    return True