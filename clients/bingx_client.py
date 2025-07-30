from clients.base import ExchangeClient
from utils.helpers import round_to_step
from config import BINGX_API_KEY, BINGX_API_SECRET
from urllib.parse import urlencode, quote
import requests
import time
import hmac
import hashlib
import json

class BingXClient(ExchangeClient):
    def __init__(self, demo: bool = False):
        self.api_key = BINGX_API_KEY
        self.api_secret = BINGX_API_SECRET
        self.demo = demo
        self.BASE_URL = "https://open-api-vst.bingx.com" if self.demo else "https://open-api.bingx.com"

    def _sign(self, params):
        sorted_params = dict(sorted(params.items()))
        query_string = urlencode(sorted_params, quote_via=quote)
        return hmac.new(self.api_secret.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256).hexdigest()

    def _request(self, method, path, body_params=None, query_params=None):
        if query_params is None:
            query_params = {}
        if body_params is None:
            body_params = {}

        query_params["timestamp"] = str(int(time.time() * 1000))
        query_params.setdefault("recvWindow", "5000")

        all_params = {**query_params, **body_params}
        signature = self._sign(all_params)
        query_params["signature"] = signature

        url = f"{self.BASE_URL}{path}?{urlencode(query_params, quote_via=quote)}"
        headers = {
            "X-BX-APIKEY": self.api_key,
            "Content-Type": "application/json"
        }

        if method.upper() == "POST":
            response = requests.post(url, headers=headers, json=body_params)
        else:
            response = requests.get(url, headers=headers)

        data = response.json()
        if data.get("code") != 0:
            raise Exception(f"BingX API error: {data}")
        return data

    def set_leverage(self, symbol, leverage, position_side):
        """Set leverage for a symbol and position side."""
        path = "/openApi/swap/v2/trade/leverage"
        body_params = {
            "symbol": symbol,
            "side": position_side.upper(),  # LONG or SHORT
            "leverage": str(int(leverage))
        }
        return self._request("POST", path, body_params=body_params)

    def get_instrument_info(self, symbol):
        """Fetch symbol information (tick size, quantity step, etc.)."""
        path = "/openApi/swap/v2/quote/contracts"
        query_params = {"symbol": symbol}
        response = self._request("GET", path, query_params=query_params)
        data = response["data"][0]  # Assuming single symbol response
        return {
            "priceFilter": {"tickSize": str(data["tickSize"])},
            "lotSizeFilter": {
                "qtyStep": str(data["quantityStep"]),
                "minOrderQty": str(data["minQuantity"]),
                "maxOrderQty": str(data["maxQuantity"])
            }
        }

    def get_price(self, symbol):
        """Fetch current market price."""
        path = "/openApi/swap/v2/quote/price"
        query_params = {"symbol": symbol}
        response = self._request("GET", path, query_params=query_params)
        return float(response["data"]["price"])

    def place_order(self, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price):
        """
        Place a market order with stop-loss and multiple take-profit limit orders.

        Args:
            symbol: Trading pair (e.g., "BTC-USDT")
            side: "Buy" or "Sell"
            leverage: Leverage multiplier
            margin_usd: Margin amount in USD
            tp_prices: List of take-profit prices
            tp_percents: List of take-profit percentages (must sum to 1.0)
            sl_price: Stop-loss price
        """
        # Validate inputs
        if len(tp_prices) != len(tp_percents):
            raise ValueError("tp_prices and tp_percents must match")
        if abs(sum(tp_percents) - 1.0) > 0.01:
            raise ValueError("TP percentages must sum to 1.0")

        # Get instrument info for precision
        instrument = self.get_instrument_info(symbol)
        tick = float(instrument["priceFilter"]["tickSize"])
        step = float(instrument["lotSizeFilter"]["qtyStep"])
        min_qty = float(instrument["lotSizeFilter"]["minOrderQty"])
        max_qty = float(instrument["lotSizeFilter"]["maxOrderQty"])

        # Calculate order quantity
        current_price = self.get_price(symbol)
        qty = round_to_step((margin_usd * leverage) / current_price, step)
        if qty < min_qty or qty > max_qty:
            raise ValueError(f"Qty {qty} is out of bounds [{min_qty}, {max_qty}]")

        sl_price = round_to_step(sl_price, tick)
        position_side = "LONG" if side.lower() == "buy" else "SHORT"
        market_side = "BUY" if side.lower() == "buy" else "SELL"

        # Set leverage
        self.set_leverage(symbol, leverage, position_side)

        # Place main market order with stop-loss
        main_order = self._request(
            method="POST",
            path="/openApi/swap/v2/trade/order",
            body_params={
                "symbol": symbol,
                "side": market_side,
                "positionSide": position_side,
                "type": "MARKET",
                "quantity": str(qty),
                "stopLoss": json.dumps({
                    "type": "STOP_MARKET",
                    "stopPrice": float(sl_price),
                    "workingType": "MARK_PRICE"
                })
            }
        )

        print(f"\n✅ Market order placed. Qty: {qty} | SL: {sl_price}\n")

        # Place TP limit orders (reduce-only)
        tp_orders = []
        tp_side = "SELL" if side.lower() == "buy" else "BUY"
        for i, (tp_price, percent) in enumerate(zip(tp_prices, tp_percents), start=1):
            tp_qty = round_to_step(qty * percent, step)
            tp_price = round_to_step(tp_price, tick)

            # Skip TP if it would trigger immediately
            price_triggered = (
                (tp_side == "SELL" and tp_price <= current_price) or
                (tp_side == "BUY" and tp_price >= current_price)
            )
            if price_triggered:
                print(f"⚠️  TP{i} @ {tp_price} would trigger immediately — skipping.")
                continue

            print(f"→ TP{i}: {tp_qty} @ {tp_price} ({int(percent * 100)}%)")
            tp_order = self._request(
                method="POST",
                path="/openApi/swap/v2/trade/order",
                body_params={
                    "symbol": symbol,
                    "side": tp_side,
                    "positionSide": position_side,
                    "type": "LIMIT",
                    "quantity": str(tp_qty),
                    "price": str(tp_price),
                    "reduceOnly": True
                }
            )
            tp_orders.append(tp_order)

        print("✅ All valid TP orders placed.\n")

        return {
            "market_order": main_order,
            "tp_orders": len(tp_orders)
        }
