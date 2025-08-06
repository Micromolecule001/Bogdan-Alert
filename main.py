from config import tp_presets, client_map

# ==== Выбор биржи ====
print("Выбери биржу:")
for i, name in enumerate(client_map.keys(), start=1):
    print(f"{i}. {name.capitalize()}")

choice = int(input("Введите номер биржи: "))
exchange_names = list(client_map.keys())

if 1 <= choice <= len(exchange_names):
    selected_exchange = exchange_names[choice - 1]
    ClientClass = client_map[selected_exchange]
    client = ClientClass()  # экземпляр класса биржи
    print(f"✅ Биржа выбрана: {selected_exchange}")
else:
    raise ValueError("Неверный выбор биржи!")

# ==== Ввод параметров ====
symbol = input("Symbol (e.g. BTCUSDT): ").strip().upper()
side = input("Side (Long/Short): ").capitalize()
leverage = int(input("Leverage (e.g. 10): "))
margin_usd = float(input("Margin USD (e.g. 100): "))

# ==== Выбор TP пресета ====
print("\nChoose TP preset:\n")
for i, preset in enumerate(tp_presets):
    print(f"{i+1}. {preset['name']}")

preset_choice = int(input("\nYour choice: ")) - 1
preset = tp_presets[preset_choice]

tp_relative = preset["take_percents"]
platform_levels = preset["platform_levels"]

def convert_relative_to_absolute(relatives):
    """Convert relative TP percentages (by remainder) to absolute weights."""
    absolutes = []
    remaining = 1.0
    for r in relatives:
        part = round(remaining * r, 6)
        absolutes.append(part)
        remaining -= part
    return absolutes

tp_percents = convert_relative_to_absolute(tp_relative) if sum(tp_relative) > 1.01 else tp_relative

# ==== Получение текущей цены и TP цен ====
price = client.get_price(symbol)
print(f"\n📈 Current price of {symbol}: {price:.2f}")

tp_prices = []
print("\nВведи цену для каждого тейк-профита:")
for i, percent in enumerate(tp_percents):
    tp_price = float(input(f"  TP {i+1} (доля {percent*100:.1f}%): "))
    tp_prices.append(tp_price)

# ==== Stop Loss ====
sl_price = float(input("SL price: "))

# ==== Размещение ордера ====
print(f"\n🛒 Placing order with:")
print(f" - TP percents: {tp_percents}")
print(f" - TP prices:   {tp_prices}")
print(f" - SL price:    {sl_price}\n")

result = client.place_order(
    symbol=symbol,
    side=side,
    leverage=leverage,
    margin_usd=margin_usd,
    tp_prices=tp_prices,
    tp_percents=tp_percents,
    sl_price=sl_price
)

print(f"\n✅ Order placed successfully! TP orders: {result['tp_orders']}")
from clients.bybit import BybitClient
from clients.binance import BinanceClient
# from clients.bingx import BingxClient  # ← добавишь, когда готов будет

from utils.helpers import round_to_step  # если нужно где-то
from config import tp_presets  # TP шаблоны

# ===== Клиент-мап =====
client_map = {
    "bybit": BybitClient,
    "binance": BinanceClient,
    # "bingx": BingxClient,
}

# ===== Выбор биржи =====
print("Выбери биржу:")
for i, name in enumerate(client_map.keys(), start=1):
    print(f"{i}. {name.capitalize()}")

try:
    choice = int(input("Введите номер биржи: "))
    exchange_names = list(client_map.keys())
    selected_exchange = exchange_names[choice - 1]
    ClientClass = client_map[selected_exchange]
    client = ClientClass()
    print(f"\n✅ Биржа выбрана: {selected_exchange}")
except (ValueError, IndexError):
    print("❌ Неверный выбор биржи.")
    exit(1)

# ===== Ввод параметров =====
symbol = input("Symbol (e.g. BTCUSDT): ").strip().upper()
side = input("Side (Long/Short): ").capitalize()
leverage = int(input("Leverage (e.g. 10): "))
margin_usd = float(input("Margin USD (e.g. 100): "))

# ===== Выбор TP пресета =====
print("\nВыбери TP пресет:\n")
for i, preset in enumerate(tp_presets):
    print(f"{i + 1}. {preset['name']}")

preset_choice = int(input("\nТвой выбор: ")) - 1
preset = tp_presets[preset_choice]
tp_relative = preset["take_percents"]
platform_levels = preset.get("platform_levels", [])  # если есть

def convert_relative_to_absolute(relatives):
    """Convert relative TP percentages (by remainder) to absolute weights."""
    absolutes = []
    remaining = 1.0
    for r in relatives:
        part = round(remaining * r, 6)
        absolutes.append(part)
        remaining -= part
    return absolutes

tp_percents = convert_relative_to_absolute(tp_relative) if sum(tp_relative) > 1.01 else tp_relative

# ===== Получение цены и ввод TP =====
try:
    price = client.get_price(symbol)
    print(f"\n📈 Текущая цена {symbol}: {price:.2f}")
except Exception as e:
    print(f"❌ Ошибка при получении цены: {e}")
    exit(1)

tp_prices = []
print("\nВведи цену для каждого тейк-профита:")
for i, percent in enumerate(tp_percents):
    try:
        tp_price = float(input(f"  TP {i + 1} (доля {percent * 100:.1f}%): "))
        tp_prices.append(tp_price)
    except ValueError:
        print("❌ Неверное значение цены.")
        exit(1)

# ===== Stop Loss =====
try:
    sl_price = float(input("SL price: "))
except ValueError:
    print("❌ Неверное значение SL.")
    exit(1)

# ===== Размещение ордера =====
print(f"\n🛒 Размещаем ордер:")
print(f" - TP проценты: {tp_percents}")
print(f" - TP цены:     {tp_prices}")
print(f" - SL цена:     {sl_price}\n")

try:
    result = client.place_order(
        symbol=symbol,
        side=side,
        leverage=leverage,
        margin_usd=margin_usd,
        tp_prices=tp_prices,
        tp_percents=tp_percents,
        sl_price=sl_price
    )

    print(f"\n✅ Ордер успешно размещён! TP ордеров: {result['tp_orders']}")

except Exception as e:
    print(f"\n❌ Ошибка при размещении ордера: {e}")

