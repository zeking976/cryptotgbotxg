import requests
from typing import Dict

def get_dex_paid(mint: str) -> bool:
    url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
    try:
        r = requests.get(url, timeout=5)
        pairs = r.json().get("pairs", [])
        for p in pairs:
            if p.get("infoUrl"):
                print(f"Paid DexScreener: {mint}")
                return True
        print(f"No paid DexScreener: {mint}")
        return False
    except Exception as e:
        print(f"DexScreener error: {e}")
        return False

def is_rug_filter(mint: str, rpc: str) -> bool:
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenLargestAccounts", "params": [mint]}
    try:
        r = requests.post(rpc.rstrip("/"), json=payload, timeout=5)
        top = r.json()["result"]["value"][0]["uiAmount"]
        if top > 0.5 * 1_000_000_000:
            print(f"Rug: {mint}")
            return False
        return True
    except Exception as e:
        print(f"Rug check failed: {e}")
        return True

def passes_filters(t: Dict, rpc: str) -> bool:
    mint = t["mint"]
    mcap, liq = t["mcap"], t["liq"]

    # 1. MCAP range
    if not (15000 < mcap < 700000):
        print(f"MCAP out: ${mcap}")
        return False

    # 2. Ratio > 10
    if liq == 0 or mcap / liq <= 10:
        print(f"Low ratio: {mcap/liq:.1f}")
        return False

    # 3. PAID DEX: Required only for trending (not new)
    if not t.get("is_new", False):
        if not get_dex_paid(mint):
            return False
    else:
        print(f"New token — skipping paid check: {mint}")

    # 4. Rug check
    if not is_rug_filter(mint, rpc):
        return False

    print(f"PASSED: {mint} | MCAP=${mcap:.0f} | Ratio={mcap/liq:.1f}")
    return True