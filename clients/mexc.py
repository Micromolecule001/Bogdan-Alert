import requests
from clients.base import ExchangeClient

class MEXCClient(ExchangeClient):
    BASE_URL = "https://api.mexc.com"

    def get_price(self, symbol: str) -> float:
        response = requests.get(f"{self.BASE_URL}/api/v3/ticker/price", params={"symbol": symbol})
        data = response.json()
        return float(data["price"])

