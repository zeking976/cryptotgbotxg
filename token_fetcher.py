import time
from typing import List, Dict
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"

class TokenFetcher:
    def __init__(self, api_key: str):
        self.transport = RequestsHTTPTransport(
            url="https://graphql.bitquery.io",
            headers={"X-API-KEY": api_key}
        )
        self.client = Client(transport=self.transport, fetch_schema_from_transport=True)
        self.last_time = time.time() - 900  # Start with 15 min window

    def get_new_pump_tokens(self) -> List[Dict]:
        since = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.last_time))
        query = gql("""
            query NewPumpTokens($since: ISO8601DateTime) {
                Solana {
                    DEXTrades(
                        where: {Transaction: {Block: {Time: {since: $since}}}, Trade: {Dex: {ProtocolFamily: {is: "pump"}}}}
                        limit: {count: 10}
                        orderBy: {descending: Block_Time}
                    ) {
                        Trade {
                            Currency { MintAddress Symbol Name }
                            Block { Time }
                            Buy { AmountInUSD }
                            Sell { AmountInUSD }
                        }
                        Transaction { Signer }  # Dev address
                    }
                }
            }
        """)
        try:
            print("Fetching new Pump.fun tokens...")
            params = {"since": since}
            result = self.client.execute(query, variable_values=params)
            trades = result["Solana"]["DEXTrades"]
            tokens = []
            now = time.time()
            for t in trades:
                ts = time.mktime(time.strptime(t["Trade"]["Block"]["Time"], "%Y-%m-%dT%H:%M:%SZ"))
                if now - ts > 15 * 60: continue  # <15 min
                mint = t["Trade"]["Currency"]["MintAddress"]
                tokens.append({
                    "mint": mint,
                    "symbol": t["Trade"]["Currency"]["Symbol"],
                    "dev": t["Transaction"]["Signer"],
                    "created_at": ts,
                    "mcap": 0,  # Fetch later
                    "liq": 0,
                    "volume_usd": float(t["Trade"].get("Buy", {}).get("AmountInUSD", 0) + t["Trade"].get("Sell", {}).get("AmountInUSD", 0))
                })
            self.last_time = now
            print(f"Fetched {len(tokens)} new Pump tokens")
            return tokens
        except Exception as e:
            print(f"New Pump fetch error: {e}")
            return []

    def get_trending_pump_tokens(self) -> List[Dict]:
        query = gql("""
            query TrendingPumpTokens {
                Solana {
                    DEXTrades(
                        where: {Trade: {Dex: {ProtocolFamily: {is: "pump"}}}, Transaction: {Block: {Time: {since: "2025-10-28T00:00:00Z"}}}}
                        limit: {count: 10}
                        orderBy: {descending: Trade_AmountInUSD}
                    ) {
                        Trade {
                            Currency { MintAddress Symbol Name }
                            Buy { AmountInUSD }
                            Sell { AmountInUSD }
                        }
                        Transaction { Signer }
                    }
                }
            }
        """)
        try:
            print("Fetching trending Pump.fun tokens...")
            result = self.client.execute(query)
            trades = result["Solana"]["DEXTrades"]
            # Dedup by mint
            unique = {}
            for t in trades:
                mint = t["Trade"]["Currency"]["MintAddress"]
                if mint not in unique:
                    unique[mint] = {
                        "mint": mint,
                        "symbol": t["Trade"]["Currency"]["Symbol"],
                        "dev": t["Transaction"]["Signer"],
                        "created_at": time.time(),  # Approx
                        "mcap": 0,
                        "liq": 0,
                        "volume_usd": float(t["Trade"].get("Buy", {}).get("AmountInUSD", 0) + t["Trade"].get("Sell", {}).get("AmountInUSD", 0))
                    }
            tokens = list(unique.values())
            print(f"Fetched {len(tokens)} trending Pump tokens")
            return tokens
        except Exception as e:
            print(f"Trending Pump fetch error: {e}")
            return []