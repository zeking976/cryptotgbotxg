import requests
import time
from typing import List, Dict

class TokenFetcher:
    def __init__(self, moralis_key: str):
        self.moralis_key = moralis_key
        self.last_time = int(time.time()) - 900  # 15 min ago

    def _headers(self):
        return {"accept": "application/json", "X-API-Key": self.moralis_key}

    def get_new_pump_tokens(self) -> List[Dict]:
        url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new?limit=30"
        try:
            print("Fetching new Pump.fun tokens...")
            r = requests.get(url, headers=self._headers(), timeout=10)
            r.raise_for_status()
            data = r.json().get("result", [])
            now = time.time()
            tokens = []
            for t in data:
                created = t.get("createdAt")
                if not created: continue
                ts = time.mktime(time.strptime(created.split(".")[0], "%Y-%m-%dT%H:%M:%S"))
                if now - ts > 15 * 60: continue  # <15 min old
                tokens.append({
                    "mint": t["tokenAddress"],
                    "created_at": ts,
                    "dev": t.get("creatorAddress", ""),
                    "mcap": float(t.get("fullyDilutedValuation") or 0),
                    "liq": float(t.get("liquidity") or 0),
                    "volume_usd": float(t.get("volume", {}).get("h1", 0))
                })
            print(f"Fetched {len(tokens)} new Pump tokens")
            self.last_time = int(now)
            return tokens
        except Exception as e:
            print(f"New Pump fetch error: {e}")
            return []

    def get_trending_pump_tokens(self) -> List[Dict]:
        url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/top-gainers-losers?limit=10&timeframe=h1"
        try:
            print("Fetching trending Pump.fun tokens...")
            r = requests.get(url, headers=self._headers(), timeout=10)
            r.raise_for_status()
            data = r.json().get("result", [])
            tokens = []
            seen = set()
            for t in data:
                mint = t["tokenAddress"]
                if mint in seen: continue
                seen.add(mint)
                tokens.append({
                    "mint": mint,
                    "created_at": time.time(),
                    "dev": t.get("creatorAddress", ""),
                    "mcap": float(t.get("fullyDilutedValuation") or 0),
                    "liq": float(t.get("liquidity") or 0),
                    "volume_usd": float(t.get("volume", {}).get("h1", 0))
                })
            print(f"Fetched {len(tokens)} trending Pump tokens")
            return tokens
        except Exception as e:
            print(f"Trending Pump fetch error: {e}")
            return []