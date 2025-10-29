import requests
import time
from typing import List, Dict

CHAIN_ID = "solana"
DEX_ID = "raydium"  # Pump.fun tokens go to Raydium

class TokenFetcher:
    def __init__(self):
        self.last_time = int(time.time()) - 900  # 15 min

    def _safe_pairs(self, data: dict) -> List[dict]:
        pairs = data.get("pairs")
        if not pairs or not isinstance(pairs, list):
            return []
        return pairs

    def get_new_tokens(self) -> List[Dict]:
        url = f"https://api.dexscreener.com/latest/dex/pairs/{CHAIN_ID}/{DEX_ID}"
        params = {"sortBy": "pairAge", "order": "asc", "perPage": 30}
        try:
            print("Fetching new Pump.fun tokens (Solana)...")
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            pairs = self._safe_pairs(r.json())
            now = time.time()
            tokens = []
            for p in pairs:
                if p.get("chainId") != CHAIN_ID: continue
                mint = p["baseToken"]["address"]
                if not mint.endswith("pump"): continue  # ONLY PUMP.FUN
                age = p.get("pairAge", 999999)
                if age > 15 * 60: continue  # <15 min
                tokens.append({
                    "mint": mint,
                    "created_at": now - age,
                    "mcap": float(p.get("fdv", 0)),
                    "liq": float(p.get("liquidity", {}).get("usd", 0)),
                    "volume_usd": float(p.get("volume", {}).get("h24", 0)),
                    "is_new": True
                })
            print(f"Fetched {len(tokens)} new Pump.fun tokens")
            return tokens
        except Exception as e:
            print(f"New fetch error: {e}")
            return []

    def get_trending_tokens(self) -> List[Dict]:
        url = "https://api.dexscreener.com/latest/dex/search"
        params = {"q": "pump", "perPage": 50}  # Search "pump" tokens
        try:
            print("Fetching trending Pump.fun tokens...")
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            pairs = self._safe_pairs(r.json())
            active = []
            for p in pairs:
                if p.get("chainId") != CHAIN_ID: continue
                mint = p["baseToken"]["address"]
                if not mint.endswith("pump"): continue
                vol = float(p.get("volume", {}).get("h24", 0))
                txns = (p.get("txns", {}).get("h24", {}).get("buys", 0) +
                        p.get("txns", {}).get("h24", {}).get("sells", 0))
                if vol < 5000 or txns < 30: continue
                active.append((p, vol))
            # Top 10 by volume
            top_pairs = [p for p, _ in sorted(active, key=lambda x: x[1], reverse=True)[:10]]
            tokens = []
            seen = set()
            for p in top_pairs:
                mint = p["baseToken"]["address"]
                if mint in seen: continue
                seen.add(mint)
                tokens.append({
                    "mint": mint,
                    "created_at": time.time(),
                    "mcap": float(p.get("fdv", 0)),
                    "liq": float(p.get("liquidity", {}).get("usd", 0)),
                    "volume_usd": float(p.get("volume", {}).get("h24", 0)),
                    "is_new": False
                })
            print(f"Fetched {len(tokens)} trending Pump.fun tokens")
            return tokens
        except Exception as e:
            print(f"Trending fetch error: {e}")
            return []