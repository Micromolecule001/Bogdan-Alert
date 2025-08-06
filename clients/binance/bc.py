# old

from clients.base import ExchangeClient
from config import BINANCE_API_KEY, BINANCE_API_SECRET
from binance.client import Client
from binance.exceptions import BinanceAPIException
from utils.helpers import round_to_step

class BinanceClient(ExchangeClient):
    def __init__(self):
        self.client = Client(api_key=BINANCE_API_KEY, api_secret=BINANCE_API_SECRET)
        self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi'  # ← важно для тестнета

    def get_price(self, symbol: str) -> float:
        ticker = self.client.futures_symbol_ticker(symbol=symbol)
        return float(ticker["price"])

    def get_instrument_info(self, symbol: str) -> dict:
        info = self.client.futures_exchange_info()
        for s in info["symbols"]:
            if s["symbol"] == symbol:
                return s
        raise ValueError(f"Symbol {symbol} not found")

    def place_order(self, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
        info = self.get_instrument_info(symbol)
        tick = float(info["filters"][0]["tickSize"])
        step = float(info["filters"][1]["stepSize"])
        min_qty = float(info["filters"][1]["minQty"])
        max_qty = float(info["filters"][1]["maxQty"])

        if len(tp_prices) != len(tp_percents):
            raise ValueError("tp_prices and tp_percents must match")
        if abs(sum(tp_percents) - 1.0) > 0.01:
            raise ValueError("TP percentages must sum to 1.0")

        current_price = self.get_price(symbol)
        qty = round_to_step((margin_usd * leverage) / current_price, step)
        if qty < min_qty or qty > max_qty:
            raise ValueError(f"Qty {qty} is out of bounds [{min_qty}, {max_qty}]")

        sl_price = round_to_step(sl_price, tick)
        self.client.futures_change_leverage(symbol=symbol, leverage=leverage)

        market_order = self.client.futures_create_order(
            symbol=symbol,
            side=side.upper(),
            type="MARKET",
            quantity=qty
        )

        print(f"\n✅ Market order placed. Qty: {qty} | SL: {sl_price}\n")

        # SL
        sl_side = "BUY" if side.upper() == "SELL" else "SELL"
        self.client.futures_create_order(
            symbol=symbol,
            side=sl_side,
            type="STOP_MARKET",
            stopPrice=str(sl_price),
            closePosition=True,
            timeInForce="GTC"
        )

        # TP
        tp_side = "SELL" if side.upper() == "BUY" else "BUY"

        for i, (tp_price, percent) in enumerate(zip(tp_prices, tp_percents), start=1):
            tp_price = round_to_step(tp_price, tick)
            tp_qty = round_to_step(qty * percent, step)

            # Пропускаем TP, который сработает сразу
            price_triggered = (
                (tp_side == "SELL" and tp_price <= current_price) or
                (tp_side == "BUY" and tp_price >= current_price)
            )

            if price_triggered:
                print(f"⚠️  TP{i} @ {tp_price} would trigger immediately — skipping.")
                continue

            try:
                print(f"→ TP{i}: {tp_qty} @ {tp_price} ({int(percent * 100)}%)")
                self.client.futures_create_order(
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

