import requests
from clients.base import ExchangeClient

class BinanceClient(ExchangeClient):
    BASE_URL = "https://api.binance.com"

    def get_price(self, symbol: str) -> float:
        response = requests.get(f"{self.BASE_URL}/api/v3/ticker/price", params={"symbol": symbol})
        data = response.json()
        return float(data["price"])

