import requests
from clients.base import ExchangeClient

class BybitClient(ExchangeClient):
    BASE_URL = "https://api.bybit.com"

    def get_price(self, symbol: str) -> float:
        response = requests.get(f"{self.BASE_URL}/v5/market/tickers", params={"category": "spot", "symbol": symbol})
        data = response.json()
        return float(data["result"]["list"][0]["lastPrice"])

