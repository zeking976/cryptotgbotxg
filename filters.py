# filters.py
import requests
from typing import Dict

def is_rug_filter(mint: str, rpc: str) -> bool:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenLargestAccounts", "params": [mint]}
    try:
        r = requests.post(rpc.rstrip("/"), json=payload, timeout=5)
        top = r.json()["result"]["value"][0]["uiAmount"]
        if top > 0.5 * 1_000_000_000:
            print(f"RUG: {mint}")
            return False
        return True
    except Exception as e:
        print(f"Rug check failed: {e}")
        return True

def passes_filters(t: Dict, rpc: str) -> bool:
    mint = t["mint"]
    mcap, liq = t["mcap"], t["liq"]

    # MCAP range
    if not (25000 < mcap < 700000):
        print(f"MCAP out: ${mcap:.0f}")
        return False

    # Ratio > 10
    if liq == 0 or mcap / liq <= 10:
        print(f"Low ratio: {mcap/liq:.1f}")
        return False

    # PAID DEX: Only for TRENDING
    if not t.get("is_new", False):
        if not t.get("has_paid_dex", False):
            print(f"No paid DexScreener (trending): {mint}")
            return False
    else:
        print(f"New token — paid Dex optional: {mint}")

    # Rug check
    if not is_rug_filter(mint, rpc):
        return False

    print(f"PASSED: {mint} | MCAP=${mcap:.0f} | Ratio={mcap/liq:.1f}")
    return True