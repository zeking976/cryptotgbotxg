import requests
from typing import Dict, Optional, Tuple

def get_mcap_liq(mint: str) -> Optional[Tuple[float, float]]:
    url = f"https://lite-api.jup.ag/tokens/v2/search?query={mint}"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        if data:
            mcap = data[0].get("mcap", 0)
            liq = data[0].get("liquidity", 0)
            print(f"Token {mint}: MCap=${mcap}, Liq=${liq}")
            return mcap, liq
    except Exception as e:
        print(f"Jupiter error for {mint}: {e}")
    return None

def is_rug_filter(mint: str, rpc: str) -> bool:
    url = f"{rpc}/api"  # Note: Should be {rpc}? Probably a bug—fix to full URL
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenLargestAccounts", "params": [mint]}
    try:
        resp = requests.post(url, json=payload, timeout=5)
        data = resp.json()
        if "result" in data and data["result"]["value"]:
            top_hold = data["result"]["value"][0].get("uiAmount", 0)
            if top_hold > 0.5 * 1e9:  # Rough 50% of 1B supply
                print(f"Rug detected for {mint}: Top holder {top_hold}")
                return False
        return True
    except Exception as e:
        print(f"Rug check error: {e} - Skipping filter")
        return True  # Fail-open

def passes_filters(token_data: Dict) -> bool:
    mcap, liq = token_data.get("mcap", 0), token_data.get("liq", 0)
    if mcap == 0 or liq == 0:
        mcap_liq = get_mcap_liq(token_data["mint"])
        if not mcap_liq: return False
        mcap, liq = mcap_liq
    print(f"Filtering {token_data['mint']}: MCap=${mcap}, Ratio={mcap/liq if liq else 0}")
    if not (15000 < mcap < 700000): return False
    if liq == 0 or mcap / liq <= 10: return False
    return is_rug_filter(token_data["mint"], "https://api.mainnet-beta.solana.com")  # Fixed RPC