import requests
from .utils import BASE, build_auth_params, round_to_step
from .info import get_price, get_instrument_info
from config import BINGX_API_KEY

def place_order(symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
    instrument = get_instrument_info(symbol)
    tick = float(instrument['tickSize'])
    step = float(instrument['lotSizeStep'])
    min_qty = float(instrument['minOrderQty'])
    max_qty = float(instrument['maxOrderQty'])

    price = get_price(symbol)
    qty = (margin_usd * leverage) / price
    qty = round_to_step(qty, step)

    if qty < min_qty or qty > max_qty:
        raise ValueError("Quantity out of bounds")

    path = "/openApi/swap/v2/trade/order"
    payload = {
        'symbol': symbol,
        'side': 'BUY' if side == 'Long' else 'SELL',
        'positionSide': side.upper(),
        'type': 'MARKET',
        'quantity': qty
    }

    params = build_auth_params(payload.copy())
    headers = {'X-BX-APIKEY': BINGX_API_KEY}

    response = requests.post(BASE + path, params=params, headers=headers)
    result = response.json()
    if result.get('code') != 0:
        raise Exception(f"Order failed: {result.get('msg')}")

    return {'market_order': result['data'], 'qty': qty}
