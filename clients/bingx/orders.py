# clients/bingx/orders.py

from bingx.api import BingxAPI
from config import BINGX_API_KEY, BINGX_API_SECRET
from .utils import map_side_for_bingx

def place_order(symbol: str, side: str, leverage: int,
                margin_usd: float, tp_prices: list,
                tp_percents: list, sl_price: float,
                price: float = None):
    """
    Размещает ордер на BingX с несколькими тейк-профитами и стоп-лоссом.

    :param symbol: Торговая пара, например 'BTC-USDT'
    :param side: LONG или SHORT
    :param leverage: Плечо
    :param margin_usd: Размер маржи в USDT
    :param tp_prices: Список цен для тейк-профита
    :param tp_percents: Доли для каждого TP (сумма должна быть 1.0)
    :param sl_price: Цена стоп-лосса
    :param price: (опционально) Текущая цена, если уже получена
    """

    client = BingxAPI(BINGX_API_KEY, BINGX_API_SECRET, timestamp="local")
    side = map_side_for_bingx(side)

    # Если цену не передали — получаем её
    if price is None:
        from .info import get_price
        price = get_price(symbol)

    qty = margin_usd * leverage / price

    # Проверки
    if abs(sum(tp_percents) - 1) > 1e-6:
        raise ValueError("TP percents must sum to 1.0")
    if len(tp_prices) != len(tp_percents):
        raise ValueError("TP prices & percents length mismatch")

    # --- Открываем маркет-ордер ---
    order_response = client.open_market_order(
        symbol,
        side.upper(),
        qty,
        tp=str(tp_prices[0]),
        sl=str(sl_price)
    )

    print("DEBUG: Market order response:", order_response)

    # Проверка структуры ответа
    if not isinstance(order_response, dict) or "data" not in order_response:
        raise RuntimeError(f"Unexpected market order response: {order_response}")

    market_order_data = order_response["data"]

    tp_orders = []

    # --- Если TP больше одного — создаём дополнительные лимитки ---
    for tp_price, tp_per in zip(tp_prices[1:], tp_percents[1:]):
        tp_qty = qty * tp_per
        limit_order = client.open_limit_order(
            symbol,
            'SELL' if side.upper() == 'LONG' else 'BUY',
            tp_qty,
            str(tp_price)
        )
        print("DEBUG: Limit order response:", limit_order)
        tp_orders.append(limit_order)

    return {
        "market_order": market_order_data,
        "tp_orders": tp_orders
    }

