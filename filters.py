import requests
from typing import Dict

def get_dex_paid(mint: str) -> bool:
    url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
    try:
        r = requests.get(url, timeout=5)
        pairs = r.json().get("pairs", [])
        for p in pairs:
            if p.get("infoUrl"):  # Paid = has infoUrl
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
            print(f"Rug: {mint} — top holder {top}")
            return False
        return True
    except Exception as e:
        print(f"Rug check failed: {e}")
        return True  # Fail-open

def passes_filters(t: Dict, rpc: str) -> bool:
    mint = t["mint"]
    mcap, liq = t["mcap"], t["liq"]

    # 1. Dex must be paid
    if not get_dex_paid(mint):
        return False

    # 2. MCAP range
    if not (20000 < mcap < 700000):
        print(f"MCAP out of range: ${mcap}")
        return False

    # 3. Ratio > 10
    if liq == 0 or mcap / liq <= 10:
        print(f"Low ratio: {mcap/liq:.1f}")
        return False

    # 4. Rug check
    if not is_rug_filter(mint, rpc):
        return False

    print(f"PASSED: {mint} | MCAP=${mcap:.0f} | Ratio={mcap/liq:.1f}")
    return True