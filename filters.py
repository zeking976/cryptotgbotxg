import requests
from typing import Dict, Tuple

def get_dex_paid(mint: str) -> bool:
    """Check if token has paid DexScreener listing (enhanced info via infoUrl)."""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        pairs = data.get("pairs", [])
        for pair in pairs:
            if pair.get("infoUrl"):  # Paid/enhanced if infoUrl present
                print(f"Paid DexScreener confirmed for {mint}")
                return True
        print(f"No paid DexScreener for {mint}")
        return False
    except Exception as e:
        print(f"DexScreener check error for {mint}: {e}")
        return False

def get_mcap_liq(mint: str) -> Tuple[float, float] | None:
    try:
        r = requests.get(f"https://lite-api.jup.ag/tokens/v2/search?query={mint}", timeout=5)
        d = r.json()[0]
        return float(d.get("mcap", 0)), float(d.get("liquidity", 0))
    except Exception as e:
        print(f"Jupiter error for {mint}: {e}")
        return None

def is_rug_filter(mint: str, rpc: str, dev: str) -> bool:
    # Enhanced: Check dev wallet for rugs (simple balance check; expand if needed)
    payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenLargestAccounts", "params": [mint]}
    try:
        r = requests.post(rpc.rstrip('/'), json=payload, timeout=5)
        top = r.json()["result"]["value"][0]["uiAmount"]
        if top > 0.5 * 1_000_000_000:
            print(f"Rug detected {mint}: Top holder {top}")
            return False
        # Bonus: Flag if dev holds >10%
        if dev:  # From Bitquery
            dev_payload = {"jsonrpc": "2.0", "id": 1, "method": "getTokenAccountBalance", "params": [dev, {"mint": mint}]}
            dev_r = requests.post(rpc.rstrip('/'), json=dev_payload, timeout=5)
            dev_hold = dev_r.json().get("result", {}).get("value", {}).get("uiAmount", 0)
            if dev_hold / 1e9 > 0.1:
                print(f"Dev hold warning {mint}: {dev_hold}")
                return False
        return True
    except Exception as e:
        print(f"Rug check error {mint}: {e}")
        return True

def passes_filters(t: Dict, rpc: str) -> bool:
    mint = t["mint"]
    # 1. Dex must be paid
    if not get_dex_paid(mint):
        print(f"Failed paid Dex check: {mint}")
        return False

    # 2. MCAP/LIQ
    mcap, liq = t.get("mcap", 0), t.get("liq", 0)
    if mcap == 0 or liq == 0:
        j = get_mcap_liq(mint)
        if not j: return False
        mcap, liq = j
        t["mcap"], t["liq"] = mcap, liq  # Cache

    print(f"Filtering {mint}: MCAP=${mcap:.0f} LIQ=${liq:.0f} R={mcap/liq:.1f} VOL=${t.get('volume_usd', 0):.0f}")

    if not (20000 < mcap < 700000): return False
    if liq == 0 or mcap / liq <= 10: return False
    return is_rug_filter(mint, rpc, t.get("dev"))