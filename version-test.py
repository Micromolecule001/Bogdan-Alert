import time
from pybit.unified_trading import HTTP
import json
import sys

API_KEY = "j1rvhLMF5mMMAIP8dH"
API_SECRET = "ObuLEljYO3mMd4FgmeFiIpc65xZix7X0lRK4"

def get_instrument_info(client, symbol):
    """Получает информацию об инструменте (tickSize, qtyStep)."""
    response = client.get_instruments_info(category="linear", symbol=symbol)
    if response["retCode"] == 0:
        instrument = response["result"]["list"][0]
        return {
            "tickSize": float(instrument["priceFilter"]["tickSize"]),
            "qtyStep": float(instrument["lotSizeFilter"]["qtyStep"]),
            "minOrderQty": float(instrument["lotSizeFilter"]["minOrderQty"]),
            "maxOrderQty": float(instrument["lotSizeFilter"]["maxOrderQty"])
        }
    else:
        raise Exception(f"Ошибка получения данных инструмента: {response['retMsg']}")

def get_order_entry_price(client, symbol, order_id):
    """Отримує ціну входу (avgPrice) для ордера."""
    # Перевірка історії ордерів (виконані)
    response = client.get_order_history(category="linear", symbol=symbol, orderId=order_id)
    if response["retCode"] == 0 and response["result"]["list"]:
        return float(response["result"]["list"][0]["avgPrice"])
    
    # Перевірка відкритих ордерів (якщо ще не виконано)
    response = client.get_open_orders(category="linear", symbol=symbol, orderId=order_id)
    if response["retCode"] == 0 and response["result"]["list"]:
        print("active order\n")
        print(response)

        return float(response["result"]["list"][0]["price"])  # запрошена ціна, не avg
    
    raise Exception("Не вдалося знайти ордер або отримати ціну входу.")

def get_current_price(client, symbol):
    """Получает текущую рыночную цену монеты."""
    response = client.get_tickers(category="linear", symbol=symbol)
    if response["retCode"] == 0:
        return float(response["result"]["list"][0]["lastPrice"])
    else:
        raise Exception(f"Ошибка получения цены: {response['retMsg']}")

def round_to_step(value, step):
    """Округляет значение до ближайшего шага (tickSize или qtyStep)."""
    return round(value / step) * step

def check_order_status(client, symbol, order_id):
    """Проверяет статус ордера."""
    response = client.get_open_orders(category="linear", symbol=symbol, orderId=order_id)
    if response["retCode"] == 0:
        orders = response["result"]["list"]
        if orders:
            return orders[0]["orderStatus"]
        return None
    else:
        raise Exception(f"Ошибка проверки статуса ордера: {response['retMsg']}")

def update_sl(client, symbol, new_sl_price, qty, position_idx=0):
    """Обновляет стоп-лосс для позиции."""
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
        print(f"Стоп-лосс обновлён до {new_sl_price} для {qty} контрактов")
    else:
        print(f"Ошибка обновления SL: {response['retMsg']}")

def place_order(symbol, side, leverage, margin_usd, tp1_price, sl_price, new_sl_price_after_tp1):
    """Размещает ордер с двумя TP и одним SL, с перемещением SL после TP1."""
    client = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET, demo=True)

    try:
        print("1")
        # Получаем информацию об инструменте
        instrument_info = get_instrument_info(client, symbol)
        tick_size = instrument_info["tickSize"]
        qty_step = instrument_info["qtyStep"]
        min_order_qty = instrument_info["minOrderQty"]
        max_order_qty = instrument_info["maxOrderQty"]
        print("2")

        # Получаем текущую цену
        current_price = get_current_price(client, symbol)
        print("3")

        # Рассчитываем размер позиции: маржа * плечо
        position_size_usd = margin_usd * leverage
        qty = position_size_usd / current_price
        qty = round_to_step(qty, qty_step)
        if qty < min_order_qty or qty > max_order_qty:
            raise Exception(f"Количество {qty} вне допустимого диапазона: min={min_order_qty}, max={max_order_qty}")

        print("tp1")

        # Округляем цены до tickSize
        tp1_price = round_to_step(tp1_price, tick_size)
        sl_price = round_to_step(sl_price, tick_size)
        new_sl_price_after_tp1 = round_to_step(new_sl_price_after_tp1, tick_size)

        print(tp1_price)

        # Устанавливаем плечо
        

        # Размещаем первый TP (50% позиции)
        tp1_qty = round_to_step(qty * 0.5, qty_step)
        response_tp1 = client.place_order(
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
        if response_tp1["retCode"] != 0:
            raise Exception(f"Ошибка создания ордера TP1: {response_tp1['retMsg']}")

        tp1_order_id = response_tp1["result"]["orderId"]
        print(f"Ордер TP1 создан: {json.dumps(response_tp1['result'], indent=2)}")

        # Мониторинг статуса TP1
        print("Мониторинг статуса TP1...")
        while True:
            status = check_order_status(client, symbol, tp1_order_id)
            if status == "Filled":
                print(f"TP1 выполнен! Обновляем SL до {new_sl_price_after_tp1}")
                entry_price = get_order_entry_price(client, symbol, tp1_order_id)
                print(entry_price)
                print(f"TP1 виконано! Оновлюємо SL до ціни входу: {entry_price}")

                update_sl(client, symbol, entry_price, qty - tp1_qty)  # оновлюємо SL для залишку позиції
                break

            elif status in ["Cancelled", "Rejected"]:
                print(f"TP1 отменён или отклонён: {status}")
                break
            time.sleep(5)

    except Exception as e:
        print(f"Ошибка: {str(e)}")

    finally:
        print('finally')

def main():
    symbol = "BTCUSDT"
    side = "Buy"
    leverage = 10
    margin_usd = 100
    tp1_price = 110000
    sl_price = 100000
    new_sl_price_after_tp1 = 108000

    if side.lower() not in ["buy", "sell"]:
        print("Ошибка: направление должно быть 'Buy' или 'Sell'")
        return

    print("still alive")
    place_order(symbol, side, leverage, margin_usd, tp1_price, sl_price, new_sl_price_after_tp1)

if __name__ == "__main__":
    main()

