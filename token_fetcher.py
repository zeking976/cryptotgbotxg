# token_fetcher.py — WORKS FOR ALL SOLANA TOKENS (Pump.fun + normal Raydium/Jupiter/etc.)
import requests
import time
from typing import List, Dict

class TokenFetcher:
    def __init__(self):
        self.last_checked = int(time.time())

    def get_recent_solana_pairs(self) -> List[dict]:
        url = "https://api.dexscreener.com/latest/dex/pairs/solana"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            pairs = r.json().get("pairs", [])
            return pairs if isinstance(pairs, list) else []
        except Exception as e:
            print(f"Error fetching Solana pairs: {e}")
            return []

    def get_new_tokens(self) -> List[Dict]:
        print("Fetching NEW Solana tokens (all, not just pump)...")
        pairs = self.get_recent_solana_pairs()
        now = time.time()
        tokens = []

        for p in pairs:
            if p.get("chainId") != "solana":
                continue

            created = p.get("pairCreatedAt", 0) / 1000
            if not created or now - created > 15 * 60:
                continue

            vol = float(p.get("volume", {}).get("h24", 0) or 0)
            if vol < 200:  # Slightly higher than before — filters trash
                continue

            mint = p["baseToken"]["address"]
            tokens.append({
                "mint": mint,
                "created_at": created,
                "mcap": float(p.get("fdv", 0) or 0),
                "liq": float(p.get("liquidity", {}).get("usd", 0) or 0),
                "volume_usd": vol,
                "url": p.get("url", ""),
                "has_paid_dex": bool(p.get("infoUrl") and "pump.fun" not in str(p.get("infoUrl", ""))),
                "is_new": True,
            })

        print(f"Found {len(tokens)} NEW Solana tokens")
        return tokens

    def get_trending_tokens(self) -> List[Dict]:
        print("Fetching TRENDING Solana tokens (all)...")
        pairs = self.get_recent_solana_pairs()
        trending = []

        for p in pairs:
            if p.get("chainId") != "solana":
                continue

            vol = float(p.get("volume", {}).get("h24", 0) or 0)
            if vol < 1500:  # Catch real movers
                continue

            txns = (p.get("txns", {}).get("h24", {}).get("buys", 0) or 0) + \
                   (p.get("txns", {}).get("h24", {}).get("sells", 0) or 0)
            if txns < 15:
                continue

            trending.append((p, vol))

        top = [p for p, _ in sorted(trending, key=lambda x: x[1], reverse=True)[:20]]
        tokens = []
        seen = set()

        for p in top:
            mint = p["baseToken"]["address"]
            if mint in seen:
                continue
            seen.add(mint)
            tokens.append({
                "mint": mint,
                "created_at": time.time(),
                "mcap": float(p.get("fdv", 0) or 0),
                "liq": float(p.get("liquidity", {}).get("usd", 0) or 0),
                "volume_usd": vol,
                "url": p.get("url", ""),
                "has_paid_dex": bool(p.get("infoUrl") and "pump.fun" not in str(p.get("infoUrl", ""))),
                "is_new": False,
            })

        print(f"Found {len(tokens)} TRENDING Solana tokens")
        return tokens