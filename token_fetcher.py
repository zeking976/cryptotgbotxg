# token_fetcher.py — MORALIS NEW TOKENS API (Early + Trending Solana, Free Key)
import requests
import time
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

MORALIS_KEY = os.getenv("MORALIS_API_KEY")

if not MORALIS_KEY:
    print("ERROR: MORALIS_API_KEY missing in t.env")

class TokenFetcher:
    def __init__(self):
        self.last_checked = int(time.time())

    def _headers(self):
        return {"accept": "application/json", "X-API-Key": MORALIS_KEY}

    def _moralis_new_tokens(self) -> List[Dict]:
        # Latest 2025 endpoint for new Solana tokens (launches on exchanges like Raydium/Pump.fun)
        url = "https://deep-index.moralis.io/api/v2.2/defi/newTokensByExchange"
        params = {"chain": "solana", "exchange": "raydium", "limit": 30}  # Raydium for Pump.fun graduates
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=10)
            r.raise_for_status()
            data = r.json().get("result", [])
            now = time.time()
            tokens = []
            for item in data:
                created = item.get("created_at_timestamp", 0) / 1000
                if now - created > 15 * 60: continue  # <15 min
                vol = item.get("volume_24h_usd", 0)
                if vol < 100: continue
                tokens.append({
                    "mint": item["address"],
                    "created_at": created,
                    "mcap": float(item.get("market_cap", 0)),
                    "liq": float(item.get("liquidity", 0)),
                    "volume_usd": vol,
                    "is_new": True,
                })
            return tokens
        except Exception as e:
            print(f"Moralis new error: {e}")
            return []

    def _moralis_trending_tokens(self) -> List[Dict]:
        # Tokenlist for trending (volume-sorted, Solana)
        url = "https://deep-index.moralis.io/api/v2.2/defi/tokenlist"
        params = {"chain": "solana", "sort_by": "volume_24h_usd", "sort_type": "desc", "limit": 20}
        try:
            r = requests.get(url, headers=self._headers(), params=params, timeout=10)
            r.raise_for_status()
            data = r.json().get("result", [])
            tokens = []
            for item in data:
                vol = item.get("volume_24h_usd", 0)
                if vol < 1500: continue
                tokens.append({
                    "mint": item["address"],
                    "created_at": time.time(),
                    "mcap": float(item.get("market_cap", 0)),
                    "liq": float(item.get("liquidity", 0)),
                    "volume_usd": vol,
                    "is_new": False,
                })
            return tokens
        except Exception as e:
            print(f"Moralis trending error: {e}")
            return []

    def get_new_tokens(self) -> List[Dict]:
        print("Fetching NEW Solana tokens (Moralis)...")
        tokens = self._moralis_new_tokens()
        print(f"Found {len(tokens)} NEW Solana tokens")
        return tokens

    def get_trending_tokens(self) -> List[Dict]:
        print("Fetching TRENDING Solana tokens (Moralis)...")
        tokens = self._moralis_trending_tokens()
        print(f"Found {len(tokens)} TRENDING Solana tokens")
        return tokens