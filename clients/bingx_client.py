import requests
from clients.base import ExchangeClient

class BingXClient(ExchangeClient):
    BASE_URL = "https://open-api.bingx.com"

    def get_price(self, symbol: str) -> float:
        response = requests.get(f"{self.BASE_URL}/openApi/spot/v1/ticker/price", params={"symbol": symbol})
        data = response.json()
        return float(data["data"]["price"])

