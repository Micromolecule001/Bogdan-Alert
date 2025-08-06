from binance.client import Client
from config import BINANCE_API_KEY, BINANCE_API_SECRET
from clients.base import ExchangeClient

from .info import get_price, get_instrument_info
from .orders import place_order

class BinanceClient(ExchangeClient):
    def __init__(self):
        self.client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)
        self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'

    def get_price(self, symbol: str) -> float:
        return get_price(self.client, symbol)

    def get_instrument_info(self, symbol: str) -> dict:
        return get_instrument_info(self.client, symbol)

    def place_order(self, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
        return place_order(self.client, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price)

