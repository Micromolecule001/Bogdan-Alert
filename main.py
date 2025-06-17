from client import get_client
from order import place_order

client = get_client()

symbol = "BTCUSDT"
side = "Buy"
leverage = 10
margin_usd = 100

tp_prices = [110000, 112000, 115000]
tp_percents = [0.6, 0.3, 0.1]
sl_price = 99000

place_order(client, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price)

