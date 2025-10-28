import requests
import time
from typing import List, Dict, Optional

class TokenFetcher:
    def __init__(self, moralis_key: str):
        self.moralis_key = moralis_key
        self.pump_last_time = 0
        self.ray_last_time = 0

    def get_new_pump_tokens(self) -> List[Dict]:
        url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new"
        params = {"limit": 10}
        headers = {"accept": "application/json", "X-API-Key": self.moralis_key}
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=5)
            data = resp.json()
            new_tokens = [t for t in data.get("result", []) if int(t.get("created_at_timestamp", 0)) > self.pump_last_time]
            self.pump_last_time = int(time.time() * 1000)
            return [{"mint": t["address"], "created_at": t.get("created_at_timestamp", 0)} for t in new_tokens]
        except Exception:
            return []

    def get_new_ray_tokens(self) -> List[Dict]:
        url = "https://api.dexscreener.com/latest/dex/pairs/solana"
        params = {"sortBy": "pairAge", "order": "asc", "perPage": 10, "withLiquidity": "true"}
        try:
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            new_tokens = []
            for pair in data.get("pairs", []):
                if "raydium" in pair.get("dexId", "").lower() and pair.get("pairAge", 999999) < 300:  # <5 min old
                    if int(pair.get("pairCreatedAt", 0)) > self.ray_last_time:
                        new_tokens.append({"mint": pair["baseToken"]["address"], "created_at": pair.get("pairCreatedAt", 0)})
            self.ray_last_time = int(time.time() * 1000)
            return new_tokens
        except Exception:
            return []