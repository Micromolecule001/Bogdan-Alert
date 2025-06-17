from market import get_instrument_info, get_current_price
from utils import round_to_step

def place_order(client, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
    instrument = get_instrument_info(client, symbol)
    print(instrument)
    tick = float(instrument["priceFilter"]["tickSize"])
    step = float(instrument["lotSizeFilter"]["qtyStep"])
    min_qty = float(instrument["lotSizeFilter"]["minOrderQty"])
    max_qty = float(instrument["lotSizeFilter"]["maxOrderQty"])

    price = get_current_price(client, symbol)
    qty = round_to_step((margin_usd * leverage) / price, step)

    if qty < min_qty or qty > max_qty:
        raise ValueError(f"Qty {qty} out of bounds: [{min_qty}, {max_qty}]")

    sl_price = round_to_step(sl_price, tick)

    # Открываем рыночный ордер на весь объём
    response = client.place_order(
        category="linear",
        symbol=symbol,
        side=side.capitalize(),
        orderType="Market",
        qty=str(qty),
        timeInForce="IOC",
        stopLoss=str(sl_price),
        slOrderType="Market",
        tpslMode="Full"  # важно, чтобы не мешали tp-шки
    )

    if response["retCode"] != 0:
        raise Exception(f"Open order failed: {response['retMsg']}")

    print("Main order placed.")

    # Выставляем 3 TP лимитками
    for price, percent in zip(tp_prices, tp_percents):
        tp_qty = round_to_step(qty * percent, step)
        price = round_to_step(price, tick)
        print(f"TP: {tp_qty} @ {price}")
        r = client.place_order(
            category="linear",
            symbol=symbol,
            side="Sell" if side == "Buy" else "Buy",
            orderType="Limit",
            qty=str(tp_qty),
            price=str(price),
            timeInForce="GTC",
            reduceOnly=True
        )
        if r["retCode"] != 0:
            raise Exception(f"TP order failed: {r['retMsg']}")
    print("All TPs placed.")

