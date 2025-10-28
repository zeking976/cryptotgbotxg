import requests
from typing import Dict, Optional

SOL_MINT = "So11111111111111111111111111111111111111112"

def get_mcap_liq(mint: str) -> Optional[Dict]:
    url = f"https://lite-api.jup.ag/tokens/v2/search?query={mint}"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data and len(data) > 0:
            return {"mcap": data[0].get("mcap", 0), "liquidity": data[0].get("liquidity", 0)}
    except Exception:
        pass
    return None

def is_rug_filter(mint: str, rpc: str) -> bool:
    # Basic rug check: Top holder <50% supply. Fetch largest accounts.
    url = f"{rpc}/api"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenLargestAccounts",
        "params": [mint]
    }
    try:
        resp = requests.post(url, json=payload, timeout=5)
        data = resp.json()
        if "result" in data and data["result"]["value"]:
            top_hold = data["result"]["value"][0]["uiAmount"] or 0
            total_supply = 1_000_000_000  # Assume standard for memecoins; adjust if needed
            if top_hold / total_supply > 0.5:
                return False  # Rug likely
        return True
    except Exception:
        return False  # Fail safe: assume not rug

def passes_filters(mint: str, rpc: str) -> bool:
    stats = get_mcap_liq(mint)
    if not stats:
        return False
    mcap = stats["mcap"]
    liq = stats["liquidity"]
    if not (10000 < mcap < 1000000):
        return False
    if liq == 0 or mcap / liq <= 10:
        return False
    return is_rug_filter(mint, rpc)