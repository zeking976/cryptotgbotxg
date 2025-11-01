import requests
import time
from typing import List, Dict


class TokenFetcher:
    def __init__(self):
        self.last_checked = int(time.time())

    def _is_pump_token(self, pair: dict) -> bool:
        base = pair.get("baseToken", {})
        return (
            pair.get("chainId") == "solana"
            and isinstance(base, dict)
            and base.get("address", "").endswith("pump")
        )

    def get_recent_solana_pairs(self) -> List[dict]:
        """
        Fetch recent Solana pairs directly from Dexscreener.
        """
        url = "https://api.dexscreener.com/latest/dex/pairs/solana"
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            pairs = data.get("pairs", [])
            return pairs if isinstance(pairs, list) else []
        except Exception as e:
            print(f"Error fetching Solana pairs: {e}")
            return []

    def get_new_tokens(self) -> List[Dict]:
        print("Fetching NEW Pump.fun tokens...")
        pairs = self.get_recent_solana_pairs()
        now = time.time()
        tokens = []

        for p in pairs:
            if not self._is_pump_token(p):
                continue

            created = p.get("pairCreatedAt", 0) / 1000
            if not created or now - created > 15 * 60:
                continue

            vol = float(p.get("volume", {}).get("h24", 0) or 0)
            if vol < 100:
                continue

            mint = p["baseToken"]["address"]
            tokens.append({
                "mint": mint,
                "created_at": created,
                "mcap": float(p.get("fdv", 0) or 0),
                "liq": float(p.get("liquidity", {}).get("usd", 0) or 0),
                "volume_usd": vol,
                "url": p.get("url"),
                "is_new": True,
            })

        print(f"✅  Found {len(tokens)} NEW Pump.fun tokens")
        return tokens

    def get_trending_tokens(self) -> List[Dict]:
        print("Fetching TRENDING Pump.fun tokens...")
        pairs = self.get_recent_solana_pairs()
        trending = []

        for p in pairs:
            if not self._is_pump_token(p):
                continue

            vol = float(p.get("volume", {}).get("h24", 0) or 0)
            if vol < 1000:
                continue

            txns = (
                (p.get("txns", {}).get("h24", {}).get("buys", 0) or 0)
                + (p.get("txns", {}).get("h24", {}).get("sells", 0) or 0)
            )
            if txns < 10:
                continue

            trending.append((p, vol))

        top = [p for p, _ in sorted(trending, key=lambda x: x[1], reverse=True)[:15]]
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
                "volume_usd": float(p.get("volume", {}).get("h24", 0) or 0),
                "url": p.get("url"),
                "is_new": False,
            })

        print(f"✅  Found {len(tokens)} TRENDING Pump.fun tokens")
        return tokens


if __name__ == "__main__":
    tf = TokenFetcher()
    new_tokens = tf.get_new_tokens()
    trending_tokens = tf.get_trending_tokens()
    print("\nNew tokens sample:", new_tokens[:3])
    print("\nTrending tokens sample:", trending_tokens[:3])