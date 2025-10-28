import time
import requests
from typing import List, Dict

BITQUERY_URL = "https://graphql.bitquery.io"
PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

class TokenFetcher:
    def __init__(self, api_key: str):
        self.headers = {
            "Content-Type": "application/json",
            "X-API-KEY": api_key
        }
        self.last_time = int(time.time()) - 900  # 15 min ago

    def _query(self, query: str, variables: dict = None) -> dict:
        payload = {"query": query, "variables": variables or {}}
        try:
            r = requests.post(BITQUERY_URL, json=payload, headers=self.headers, timeout=10)
            r.raise_for_status()
            return r.json().get("data", {})
        except Exception as e:
            print(f"Bitquery request error: {e}")
            return {}

    def get_new_pump_tokens(self) -> List[Dict]:
        since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.last_time))
        query = """
        query($since: ISO8601DateTime) {
          Solana {
            DEXTrades(
              where: {
                Transaction: {Block: {Time: {after: $since}}},
                Trade: {Dex: {ProtocolFamily: {is: "pump"}}}
              }
              limit: {count: 10}
              orderBy: {descending: Block_Time}
            ) {
              Trade { Currency { MintAddress } Block { Time } }
              Transaction { Signer }
            }
          }
        }
        """
        data = self._query(query, {"since": since})
        trades = data.get("Solana", {}).get("DEXTrades", [])
        tokens = []
        now = time.time()
        for t in trades:
            block_time = t["Trade"]["Block"]["Time"]
            ts = time.mktime(time.strptime(block_time.split(".")[0], "%Y-%m-%dT%H:%M:%S"))
            if now - ts > 15 * 60: continue
            mint = t["Trade"]["Currency"]["MintAddress"]
            tokens.append({
                "mint": mint,
                "created_at": ts,
                "dev": t["Transaction"]["Signer"],
                "mcap": 0,
                "liq": 0,
                "volume_usd": 0
            })
        self.last_time = int(now)
        print(f"Fetched {len(tokens)} new Pump tokens")
        return tokens

    def get_trending_pump_tokens(self) -> List[Dict]:
        query = """
        query {
          Solana {
            DEXTrades(
              where: {
                Trade: {Dex: {ProtocolFamily: {is: "pump"}}},
                Transaction: {Block: {Time: {since: "2025-10-28T00:00:00Z"}}}
              }
              limit: {count: 10}
              orderBy: {descending: Trade_AmountInUSD}
            ) {
              Trade { Currency { MintAddress } Buy { AmountInUSD } Sell { AmountInUSD } }
              Transaction { Signer }
            }
          }
        }
        """
        data = self._query(query)
        trades = data.get("Solana", {}).get("DEXTrades", [])
        seen = set()
        tokens = []
        for t in trades:
            mint = t["Trade"]["Currency"]["MintAddress"]
            if mint in seen: continue
            seen.add(mint)
            vol = (t["Trade"].get("Buy", {}).get("AmountInUSD", 0) or 0) + \
                  (t["Trade"].get("Sell", {}).get("AmountInUSD", 0) or 0)
            tokens.append({
                "mint": mint,
                "created_at": time.time(),
                "dev": t["Transaction"]["Signer"],
                "mcap": 0,
                "liq": 0,
                "volume_usd": float(vol)
            })
        print(f"Fetched {len(tokens)} trending Pump tokens")
        return tokens