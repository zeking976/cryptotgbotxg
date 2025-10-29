import requests
import time
from typing import List, Dict

CHAIN_ID = "solana"
RAYDIUM_DEX = "raydium"  # For Pump.fun graduates

class TokenFetcher:
    def __init__(self):
        self.last_time = int(time.time()) - 900  # 15 min window

    def get_new_tokens(self) -> List[Dict]:
        url = f"https://api.dexscreener.com/latest/dex/pairs/{CHAIN_ID}/{RAYDIUM_DEX}"
        params = {"sortBy": "pairAge", "order": "asc", "perPage": 20}  # Newest first
        try:
            print("Fetching new/early DexScreener tokens...")
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            pairs = r.json().get("pairs", [])
            now = time.time()
            tokens = []
            for p in pairs:
                age = p.get("pairAge", 999999)  # Seconds
                if age > 15 * 60 or age == 0: continue  # <15 min, active
                mint = p["baseToken"]["address"]
                tokens.append({
                    "mint": mint,
                    "created_at": now - age,
                    "dev": "",  # Not in DexScreener; rug uses top holder
                    "mcap": float(p.get("fdv", 0)),
                    "liq": float(p.get("liquidity", {}).get("usd", 0)),
                    "volume_usd": float(p.get("volume", {}).get("h24", 0))
                })
            print(f"Fetched {len(tokens)} new/early tokens")
            self.last_time = int(now)
            return tokens
        except Exception as e:
            print(f"New DexScreener fetch error: {e}")
            return []

    def get_trending_tokens(self) -> List[Dict]:
        url = f"https://api.dexscreener.com/latest/dex/search?q={CHAIN_ID}"
        params = {"perPage": 50}  # Broader search
        try:
            print("Fetching trending/active DexScreener tokens...")
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            pairs = r.json().get("pairs", [])
            # Sort by 24h volume desc, filter active (>5k vol, >50 txns)
            active_pairs = [p for p in pairs if float(p.get("volume", {}).get("h24", 0)) > 5000 and p.get("txns", {}).get("h24", {}).get("buys", 0) + p.get("txns", {}).get("h24", {}).get("sells", 0) > 50]
            sorted_pairs = sorted(active_pairs, key=lambda p: float(p.get("volume", {}).get("h24", 0)), reverse=True)[:10]
            tokens = []
            seen = set()
            for p in sorted_pairs:
                mint = p["baseToken"]["address"]
                if mint in seen: continue
                seen.add(mint)
                tokens.append({
                    "mint": mint,
                    "created_at": time.time(),
                    "dev": "",
                    "mcap": float(p.get("fdv", 0)),
                    "liq": float(p.get("liquidity", {}).get("usd", 0)),
                    "volume_usd": float(p.get("volume", {}).get("h24", 0))
                })
            print(f"Fetched {len(tokens)} trending/active tokens")
            return tokens
        except Exception as e:
            print(f"Trending DexScreener fetch error: {e}")
            return []