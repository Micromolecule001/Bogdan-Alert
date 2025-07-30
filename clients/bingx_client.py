from bingX import BingX
from config import BINGX_API_KEY, BINGX_API_SECRET
from utils.helpers import round_to_step
from clients.base import ExchangeClient
from enum import Enum


class PositionSide(Enum):
    LONG = "LONG"
    SHORT = "SHORT"


class BingXClient(ExchangeClient):
    def __init__(self):
        self.api = BingX(api_key=BINGX_API_KEY, secret_key=BINGX_API_SECRET)
        self.perp = self.api.perpetual_v2
        self.symbol_map = self._load_symbols()

    def _load_symbols(self) -> dict:
        contracts = self.perp.market.get_contract_info()
        return {item["symbol"]: item for item in contracts}

    def normalize_symbol(self, symbol: str) -> str:
        symbol = symbol.upper().replace("--", "-")
        if symbol in self.symbol_map:
            return symbol
        if symbol.endswith("USDT") and symbol.replace("USDT", "-USDT") in self.symbol_map:
            return symbol.replace("USDT", "-USDT")
        if symbol.endswith("USDC") and symbol.replace("USDC", "-USDC") in self.symbol_map:
            return symbol.replace("USDC", "-USDC")
        raise ValueError(f"⛔ Символ {symbol} не найден на BingX Perpetual")

    def get_price(self, symbol: str) -> float:
        sym = self.normalize_symbol(symbol)
        res = self.perp.market.get_ticker(sym)
        return float(res["lastPrice"])

    def get_instrument_info(self, symbol: str) -> dict:
        sym = self.normalize_symbol(symbol)
        info = self.symbol_map[sym]

        tick_size = float(f"1e-{info.get('pricePrecision', 2)}")
        step_size = float(f"1e-{info.get('quantityPrecision', 4)}")

        missing_fields = []
        min_qty = info.get("minQty")
        max_qty = info.get("maxQty")

        if min_qty is None:
            missing_fields.append("minQty")
        if max_qty is None:
            missing_fields.append("maxQty")

        if missing_fields:
            print(f"⚠️ Биржа не вернула следующие параметры для {sym}: {', '.join(missing_fields)}")
            confirm = input("❓ Использовать резервные значения? (0.001 / 1000) [y/N]: ").strip().lower()
            if confirm != "y":
                raise ValueError("⛔ Операция отменена пользователем.")
            min_qty = 0.001
            max_qty = 1000
            print(f"✅ Используем minQty={min_qty}, maxQty={max_qty}")

        return {
            "tickSize": tick_size,
            "stepSize": step_size,
            "minQty": float(min_qty),
            "maxQty": float(max_qty),
        }

    def place_order(self, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
        sym = self.normalize_symbol(symbol)
        print(f"‼️ Normalized symbol: {sym}")

        info = self.get_instrument_info(sym)
        tick = info["tickSize"]
        step = info["stepSize"]

        price = self.get_price(sym)
        qty = round_to_step((margin_usd * leverage) / price, step)

        position_side = PositionSide.LONG if side.lower() == "buy" else PositionSide.SHORT
        self.perp.trade.change_leverage(
            symbol=sym,
            leverage=str(leverage),
            position_side=position_side
        )

        self.perp.trade.create_order(
            symbol=sym,
            side="BUY" if side.lower() == "buy" else "SELL",
            type="MARKET",
            quantity=str(qty),
            stopLoss=str(round_to_step(sl_price, tick))
        )

        if res_main.get("code") != 0:
            raise Exception("Main order failed: " + res_main.get("msg", ""))
        print(f"✅ Main market order placed: {qty} @ SL {round_to_step(sl_price, tick)}")

        for i, (tp_price, percent) in enumerate(zip(tp_prices, tp_percents), start=1):
            tp_qty = round_to_step(qty * percent, step)
            tp_pr = round_to_step(tp_price, tick)
            close_side = "SELL" if side.lower() == "buy" else "BUY"
            res_tp = self.perp.trade.create_order(Order(
                symbol=sym,
                side=close_side,
                type="LIMIT",
                price=str(tp_pr),
                quantity=str(tp_qty),
                reduceOnly=True,
                timeInForce="GTC"
            ))
            if res_tp.get("code") != 0:
                print(f"⚠️ TP{i} failed:", res_tp.get("msg", ""))
            else:
                print(f"→ TP{i} placed: {tp_qty}@{tp_pr}")

        print("🎯 All TP orders placed.")
        return {"main": res_main, "tp_count": len(tp_prices)}

