import requests
import time
from typing import List, Dict

class TokenFetcher:
    def __init__(self):
        self.last_time = int(time.time() * 1000)  # ms for comparison

    def _safe_pairs(self, data: dict) -> List[dict]:
        pairs = data.get("pairs")
        if not isinstance(pairs, list):
            return []
        return pairs

    def _is_pump_solana(self, pair: dict) -> bool:
        return (pair.get("chainId") == "solana" and 
                pair["baseToken"]["address"].endswith("pump"))

    def get_new_tokens(self) -> List[Dict]:
        url = "https://api.dexscreener.com/latest/dex/search"
        params = {"q": "pump", "perPage": 50}
        try:
            print("Fetching NEW Pump.fun tokens...")
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            pairs = self._safe_pairs(r.json())
            now = time.time()
            tokens = []
            for p in pairs:
                if not self._is_pump_solana(p): continue
                pair_created = p.get("pairCreatedAt", 0) / 1000  # ms to seconds
                age = now - pair_created
                if age > 15 * 60: continue  # <15 min
                vol = float(p.get("volume", {}).get("h24", 0))
                if vol < 500: continue  # Min $500 vol
                mint = p["baseToken"]["address"]
                tokens.append({
                    "mint": mint,
                    "created_at": pair_created,
                    "mcap": float(p.get("fdv", 0)),
                    "liq": float(p.get("liquidity", {}).get("usd", 0)),
                    "volume_usd": vol,
                    "has_paid_dex": bool(p.get("infoUrl") and "pump.fun" not in p.get("infoUrl", "")),
                    "is_new": True
                })
            print(f"Fetched {len(tokens)} NEW Pump tokens")
            return tokens
        except Exception as e:
            print(f"New fetch error: {e}")
            return []

    def get_trending_tokens(self) -> List[Dict]:
        url = "https://api.dexscreener.com/latest/dex/search"
        params = {"q": "pump", "perPage": 60}
        try:
            print("Fetching TRENDING Pump.fun tokens...")
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            pairs = self._safe_pairs(r.json())
            active = []
            for p in pairs:
                if not self._is_pump_solana(p): continue
                vol = float(p.get("volume", {}).get("h24", 0))
                txns = (p.get("txns", {}).get("h24", {}).get("buys", 0) +
                        p.get("txns", {}).get("h24", {}).get("sells", 0))
                if vol < 1000 or txns < 10: continue  # Lowered
                active.append((p, vol))
            top_pairs = [p for p, _ in sorted(active, key=lambda x: x[1], reverse=True)[:15]]
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
                    "has_paid_dex": bool(p.get("infoUrl") and "pump.fun" not in p.get("infoUrl", "")),
                    "is_new": False
                })
            print(f"Fetched {len(tokens)} TRENDING Pump tokens")
            return tokens
        except Exception as e:
            print(f"Trending fetch error: {e}")
            return []