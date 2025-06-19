from market import get_instrument_info, get_current_price
from utils import round_to_step

def place_order(client, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
    """
    Places a market order with partial TP targets using separate limit reduce-only orders.

    Args:
        client: pybit client instance
        symbol: trading pair (e.g., "BTCUSDT")
        side: "Buy" or "Sell"
        leverage: leverage multiplier
        margin_usd: amount of margin in USD
        tp_prices: list of TP prices (must match tp_percents)
        tp_percents: list of TP weights (must sum to 1.0)
        sl_price: stop-loss price
    """
    instrument = get_instrument_info(client, symbol)
    tick = float(instrument["priceFilter"]["tickSize"])
    step = float(instrument["lotSizeFilter"]["qtyStep"])
    min_qty = float(instrument["lotSizeFilter"]["minOrderQty"])
    max_qty = float(instrument["lotSizeFilter"]["maxOrderQty"])

    # Validate take-profit plan
    if len(tp_prices) != len(tp_percents):
        raise ValueError("tp_prices and tp_percents must have the same length")
    if abs(sum(tp_percents) - 1.0) > 0.01:
        raise ValueError("TP percentages must sum to 1.0")

    current_price = get_current_price(client, symbol)
    qty = round_to_step((margin_usd * leverage) / current_price, step)
    if qty < min_qty or qty > max_qty:
        raise ValueError(f"Order qty {qty} out of bounds [{min_qty}, {max_qty}]")

    sl_price = round_to_step(sl_price, tick)

    # Place main market order
    main_order = client.place_order(
        category="linear",
        symbol=symbol,
        side=side.capitalize(),
        orderType="Market",
        qty=str(qty),
        timeInForce="IOC",
        stopLoss=str(sl_price),
        slOrderType="Market",
        tpslMode="Partial"  # enables manual TP control
    )

    if main_order["retCode"] != 0:
        raise Exception(f"Main order failed: {main_order['retMsg']}")
    
    print(f"✅ Market order placed. Qty: {qty} | SL: {sl_price}\n")

    # Place TP limit orders (reduce-only)
    for i, (price, percent) in enumerate(zip(tp_prices, tp_percents), start=1):
        tp_qty = round_to_step(qty * percent, step)
        tp_price = round_to_step(price, tick)
        tp_side = "Sell" if side.lower() == "buy" else "Buy"

        print(f"→ TP{i}: {tp_qty} @ {tp_price} ({int(percent * 100)}%)")

        tp_order = client.place_order(
            category="linear",
            symbol=symbol,
            side=tp_side,
            orderType="Limit",
            qty=str(tp_qty),
            price=str(tp_price),
            timeInForce="GTC",
            reduceOnly=True
        )

        if tp_order["retCode"] != 0:
            raise Exception(f"TP{i} order failed: {tp_order['retMsg']}")
    
    print("✅ All TP orders placed successfully.\n")

    return {
        "market_order": main_order,
        "tp_orders": len(tp_prices)
    }

