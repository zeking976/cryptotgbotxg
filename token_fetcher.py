import requests
import time
from typing import List, Dict

class TokenFetcher:
    def __init__(self, moralis_key: str):
        self.moralis_key = moralis_key
        self.last_fetch = 0

    def get_new_pump_tokens(self) -> List[Dict]:
        url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new"
        params = {"limit": 5}  # Smaller for speed
        headers = {"accept": "application/json", "X-API-Key": self.moralis_key}
        try:
            print("Fetching Pump.fun tokens...")
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            tokens = data.get("result", [])
            print(f"Fetched {len(tokens)} Pump tokens")
            # Filter "new" by recent creation (last 5 min)
            recent = [t for t in tokens if (time.time() - time.mktime(time.strptime(t.get("createdAt", ""), "%Y-%m-%dT%H:%M:%S.%fZ"))) < 300]
            return [{"mint": t["tokenAddress"], "mcap": float(t.get("fullyDilutedValuation", 0)), "liq": float(t.get("liquidity", 0))} for t in recent]
        except Exception as e:
            print(f"Pump fetch error: {e}")
            return []

    def get_new_ray_tokens(self) -> List[Dict]:
        url = "https://api.dexscreener.com/latest/dex/pairs/solana"
        params = {"sortBy": "pairAge", "order": "asc", "perPage": 5}
        try:
            print("Fetching Raydium tokens...")
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            pairs = data.get("pairs", [])
            new_tokens = [{"mint": p["baseToken"]["address"], "mcap": 0, "liq": float(p.get("liquidity", {}).get("usd", 0))} for p in pairs if "raydium" in p.get("dexId", "").lower() and p.get("pairAge") < 300]
            print(f"Fetched {len(new_tokens)} Ray tokens")
            return new_tokens
        except Exception as e:
            print(f"Ray fetch error: {e}")
            return []