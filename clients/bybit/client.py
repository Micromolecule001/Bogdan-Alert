from clients.base import ExchangeClient
from config import BYBIT_API_KEY, BYBIT_API_SECRET
from pybit.unified_trading import HTTP

from .info import get_price, get_instrument_info
from .orders import place_order

class BybitClient(ExchangeClient):
    def __init__(self):
        self.client = HTTP(
            testnet=False,
            api_key=BYBIT_API_KEY,
            api_secret=BYBIT_API_SECRET,
            demo=True
        )

    def get_price(self, symbol: str) -> float:
        return get_price(self.client, symbol)

    def get_instrument_info(self, symbol: str) -> dict:
        return get_instrument_info(self.client, symbol)

    def place_order(self, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
        return place_order(self.client, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price)

