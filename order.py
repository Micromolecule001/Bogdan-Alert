import time
import json
from utils import round_to_step
from market import get_instrument_info, get_current_price

def check_order_status(client, symbol, order_id):
    response = client.get_open_orders(category="linear", symbol=symbol, orderId=order_id)
    if response["retCode"] == 0:
        orders = response["result"]["list"]
        return orders[0]["orderStatus"] if orders else None
    raise Exception(f"Status check error: {response['retMsg']}")

def get_entry_price(client, symbol):
    response = client.get_positions(category="linear", symbol=symbol)
    if response["retCode"] == 0:
        positions = response["result"]["list"]
        print(positions)
        for pos in positions:
            if float(pos["size"]) > 0:  # Active position
                return float(pos["avgPrice"])
        raise ValueError("No active position found.")
    else:
        raise Exception(f"Failed to get position info: {response['retMsg']}")

def update_sl(client, symbol, new_sl_price, qty, position_idx=0):
    response = client.set_trading_stop(
        category="linear",
        symbol=symbol,
        stopLoss=str(new_sl_price),
        slTriggerBy="MarkPrice",
        slSize=str(qty),
        tpslMode="Partial",
        slOrderType="Market",
        positionIdx=position_idx
    )
    if response["retCode"] == 0:
        print(f"SL updated to {new_sl_price} for {qty} contracts")
    else:
        print(f"SL update error: {response['retMsg']}")

def place_order(client, symbol, side, leverage, margin_usd, tp1_price, sl_price, new_sl_price_after_tp1):
    instrument = get_instrument_info(client, symbol)
    tick = instrument["tickSize"]
    step = instrument["qtyStep"]
    min_qty = instrument["minOrderQty"]
    max_qty = instrument["maxOrderQty"]

    price = get_current_price(client, symbol)
    qty = round_to_step(margin_usd * leverage / price, step)
    if qty < min_qty or qty > max_qty:
        raise Exception(f"Qty {qty} out of bounds: [{min_qty}, {max_qty}]")

    tp1_price = round_to_step(tp1_price, tick)
    sl_price = round_to_step(sl_price, tick)
    new_sl_price_after_tp1 = round_to_step(new_sl_price_after_tp1, tick)

    tp1_qty = round_to_step(qty * 0.5, step)
    response = client.place_order(
        category="linear",
        symbol=symbol,
        side=side.capitalize(),
        orderType="Market",
        qty=str(tp1_qty),
        timeInForce="IOC",
        takeProfit=str(tp1_price),
        stopLoss=str(sl_price),
        tpOrderType="Market",
        slOrderType="Market",
        tpslMode="Partial"
    )
    if response["retCode"] != 0:
        raise Exception(f"TP1 order error: {response['retMsg']}")

    tp1_id = response["result"]["orderId"]
    print(f"TP1 placed: {json.dumps(response['result'], indent=2)}")

    while True:
        status = check_order_status(client, symbol, tp1_id)
        if status == "Filled":
            print("TP1 hit — moving SL")
            entry_price = get_entry_price(client, symbol)
            update_sl(client, symbol, entry_price, qty - tp1_qty)
            break
        elif status in ["Cancelled", "Rejected"]:
            print(f"TP1 order {status}")
            break
        time.sleep(5)
