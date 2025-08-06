from clients.base import ExchangeClient
from .info import get_price, get_instrument_info
from .orders import place_order

class BingxClient(ExchangeClient):
    def get_price(self, symbol: str) -> float:
        return get_price(symbol)

    def get_instrument_info(self, symbol: str) -> dict:
        return get_instrument_info(symbol)

    def place_order(self, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
        return place_order(symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price)

