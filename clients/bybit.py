from clients.base import ExchangeClient
from pybit.unified_trading import HTTP
from config import API_KEY, API_SECRET  # ✅ правильный импорт
from utils import round_to_step

class BybitClient(ExchangeClient):
    def __init__(self):
        self.client = HTTP(
            testnet=False,
            api_key=API_KEY,
            api_secret=API_SECRET,
            demo=True
        )

    def get_price(self, symbol: str) -> float:
        response = self.client.get_tickers(category="linear", symbol=symbol)
        return float(response["result"]["list"][0]["lastPrice"])

    def get_instrument_info(self, symbol: str) -> dict:
        response = self.client.get_instruments_info(category="linear", symbol=symbol)
        return response["result"]["list"][0]

    def place_order(self, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
        instrument = self.get_instrument_info(symbol)
        tick = float(instrument["priceFilter"]["tickSize"])
        step = float(instrument["lotSizeFilter"]["qtyStep"])
        min_qty = float(instrument["lotSizeFilter"]["minOrderQty"])
        max_qty = float(instrument["lotSizeFilter"]["maxOrderQty"])

        # Проверка TP
        if len(tp_prices) != len(tp_percents):
            raise ValueError("tp_prices and tp_percents must match")
        if abs(sum(tp_percents) - 1.0) > 0.01:
            raise ValueError("TP percentages must sum to 1.0")

        current_price = self.get_price(symbol)
        qty = round_to_step((margin_usd * leverage) / current_price, step)
        if qty < min_qty or qty > max_qty:
            raise ValueError(f"Qty {qty} is out of bounds [{min_qty}, {max_qty}]")

        sl_price = round_to_step(sl_price, tick)
        market_side = "Buy" if side.lower() == "buy" else "Sell"

        # === Main order ===
        main_order = self.client.place_order(
            category="linear",
            symbol=symbol,
            side=market_side,
            orderType="Market",
            qty=str(qty),
            timeInForce="IOC",
            stopLoss=str(sl_price),
            slOrderType="Market",
            tpslMode="Partial"
        )

        if main_order["retCode"] != 0:
            raise Exception(f"Main order failed: {main_order['retMsg']}")

        print(f"\n✅ Market order placed. Qty: {qty} | SL: {sl_price}\n")

        # === TP Orders ===
        for i, (price, percent) in enumerate(zip(tp_prices, tp_percents), start=1):
            tp_qty = round_to_step(qty * percent, step)
            tp_price = round_to_step(price, tick)
            tp_side = "Sell" if market_side == "Buy" else "Buy"

            print(f"→ TP{i}: {tp_qty} @ {tp_price} ({int(percent * 100)}%)")

            tp_order = self.client.place_order(
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

        print("✅ All TP orders placed.\n")

        return {
            "market_order": main_order,
            "tp_orders": len(tp_prices)
        }
