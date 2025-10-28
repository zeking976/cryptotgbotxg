# token_fetcher.py  (full file – just copy-paste)
import requests
import time
from typing import List, Dict

class TokenFetcher:
    def __init__(self, moralis_key: str):
        self.moralis_key = moralis_key
        self.last_fetch = 0

    # ── PUMP.FUN ─────────────────────────────────────────────────────
    def get_new_pump_tokens(self) -> List[Dict]:
        url = "https://solana-gateway.moralis.io/token/mainnet/exchange/pumpfun/new"
        headers = {"accept": "application/json", "X-API-Key": self.moralis_key}
        try:
            print("Fetching Pump.fun tokens...")
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json().get("result", [])
            print(f"Fetched {len(data)} Pump tokens")
            return [
                {
                    "mint": t["tokenAddress"],
                    "mcap": float(t.get("fullyDilutedValuation", 0)),
                    "liq":  float(t.get("liquidity", 0))
                }
                for t in data
            ]
        except Exception as e:
            print(f"Pump fetch error: {e}")
            return []

    # ── RAYDIUM (NEW ENDPOINT) ───────────────────────────────────────
    def get_new_ray_tokens(self) -> List[Dict]:
        # Dexscreener “new pairs” endpoint (works today)
        url = "https://api.dexscreener.com/latest/dex/search"
        params = {"q": "raydium", "limit": 5}
        try:
            print("Fetching Raydium tokens...")
            r = requests.get(url, params=params, timeout=5)
            r.raise_for_status()
            pairs = r.json().get("pairs", [])
            new = []
            for p in pairs:
                if p.get("dexId", "").lower() != "raydium": continue
                # pairAge is in seconds – keep only <5 min old
                if p.get("pairAge", 999999) > 300: continue
                new.append({
                    "mint": p["baseToken"]["address"],
                    "mcap": 0,                     # we’ll fetch via Jupiter later
                    "liq":  float(p.get("liquidity", {}).get("usd", 0))
                })
            print(f"Fetched {len(new)} Ray tokens")
            return new
        except Exception as e:
            print(f"Ray fetch error: {e}")
            return []