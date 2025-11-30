# token_fetcher.py — MORALIS FOR NEW/TRENDING SOLANA TOKENS (Working 2025, Free Key)
import requests
import time
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

MORALIS_KEY = os.getenv("MORALIS_API_KEY")

class TokenFetcher:
    def __init__(self):
        self.last_checked = int(time.time())

    def _moralis_new_tokens(self) -> List[Dict]:
        # Moralis Pump.fun new launches (dedicated for early tokens)
        url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new"
        headers = {"accept": "application/json", "X-API-Key": MORALIS_KEY}
        params = {"limit": 30}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            r.raise_for_status()
            data = r.json().get("result", [])
            now = time.time()
            tokens = []
            for item in data:
                created = item.get("createdAtTimestamp", 0) / 1000
                if now - created > 15 * 60: continue  # <15 min
                vol = item.get("volume", {}).get("h1", 0)
                if vol < 100: continue
                tokens.append({
                    "mint": item["tokenAddress"],
                    "created_at": created,
                    "mcap": float(item.get("fullyDilutedValuation", 0) or 0),
                    "liq": float(item.get("liquidity", 0)),
                    "volume_usd": vol,
                    "is_new": True,
                })
            return tokens
        except Exception as e:
            print(f"Moralis new error: {e}")
            return []

    def _moralis_trending_tokens(self) -> List[Dict]:
        # Moralis top gainers as trending (volume-sorted)
        url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/top-gainers-losers"
        headers = {"accept": "application/json", "X-API-Key": MORALIS_KEY}
        params = {"limit": 20, "timeframe": "h1"}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=10)
            r.raise_for_status()
            data = r.json().get("result", [])
            tokens = []
            for item in data:
                vol = item.get("volume", {}).get("h1", 0)
                if vol < 1500: continue
                tokens.append({
                    "mint": item["tokenAddress"],
                    "created_at": time.time(),
                    "mcap": float(item.get("fullyDilutedValuation", 0) or 0),
                    "liq": float(item.get("liquidity", 0)),
                    "volume_usd": vol,
                    "is_new": False,
                })
            return tokens
        except Exception as e:
            print(f"Moralis trending error: {e}")
            return []

    def get_new_tokens(self) -> List[Dict]:
        print("Fetching NEW Solana tokens (Moralis Pump.fun)...")
        tokens = self._moralis_new_tokens()
        print(f"Found {len(tokens)} NEW Solana tokens")
        return tokens

    def get_trending_tokens(self) -> List[Dict]:
        print("Fetching TRENDING Solana tokens (Moralis gainers)...")
        tokens = self._moralis_trending_tokens()
        print(f"Found {len(tokens)} TRENDING Solana tokens")
        return tokens