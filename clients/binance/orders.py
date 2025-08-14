from utils.helpers import round_to_step
from binance.exceptions import BinanceAPIException

def place_order(client, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
    '''
        Algorithm:
        
        Get info for variables [ tick ; step ; min_qty ; max_qty ; current_price ]
        Handle errors
        Place main order
        Stop Loss
        Place all TP orders
    '''

    info = client.futures_exchange_info()
    symbol_info = next((s for s in info["symbols"] if s["symbol"] == symbol), None)

    if not symbol_info:
        raise ValueError(f"Symbol {symbol} not found")

    tick = float(symbol_info["filters"][0]["tickSize"])
    step = float(symbol_info["filters"][1]["stepSize"])
    min_qty = float(symbol_info["filters"][1]["minQty"])
    max_qty = float(symbol_info["filters"][1]["maxQty"])

    current_price = float(client.futures_symbol_ticker(symbol=symbol)["price"])

    qty = round_to_step((margin_usd * leverage) / current_price, step)
    sl_price = round_to_step(sl_price, tick)
    client.futures_change_leverage(symbol=symbol, leverage=leverage)

    if len(tp_prices) != len(tp_percents):
        raise ValueError("tp_prices and tp_percents must match")
    if abs(sum(tp_percents) - 1.0) > 0.01:
        raise ValueError("TP percentages must sum to 1.0")
    if qty < min_qty or qty > max_qty:
        raise ValueError(f"Qty {qty} is out of bounds [{min_qty}, {max_qty}]")

    # Main order
    market_order = client.futures_create_order(
        symbol=symbol,
        side=side.upper(),
        type="MARKET",
        quantity=qty
    )

    print(f"\n✅ Market order placed. Qty: {qty} | SL: {sl_price}\n")

    
    # Stop loss
    sl_side = "BUY" if side.upper() == "SELL" else "SELL"

    client.futures_create_order(
        symbol=symbol,
        side=sl_side,
        type="STOP_MARKET",
        stopPrice=str(sl_price),
        closePosition=True,
        timeInForce="GTC"
    )

    
    # TPs orders 
    tp_side = "SELL" if side.upper() == "BUY" else "BUY"

    for i, (tp_price, percent) in enumerate(zip(tp_prices, tp_percents), start=1):
        tp_price = round_to_step(tp_price, tick)
        tp_qty = round_to_step(qty * percent, step)

        price_triggered = (
            (tp_side == "SELL" and tp_price <= current_price) or
            (tp_side == "BUY" and tp_price >= current_price)
        )

        if price_triggered:
            print(f"⚠️  TP{i} @ {tp_price} would trigger immediately — skipping.")
            continue

        try:
            print(f"→ TP{i}: {tp_qty} @ {tp_price} ({int(percent * 100)}%)")
            client.futures_create_order(
                symbol=symbol,
                side=tp_side,
                type="LIMIT",
                quantity=tp_qty,
                price=str(tp_price),
                timeInForce="GTC",
                reduceOnly=True
            )
        except BinanceAPIException as e:
            print(f"❌ Failed to place TP{i}: {e.message}")

    print("✅ All valid TP orders placed.\n")

    return {
        "market_order": market_order,
        "tp_orders": len(tp_prices)
    }

