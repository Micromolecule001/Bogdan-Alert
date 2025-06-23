from client import get_client
from market import get_current_price
from order import place_order

def convert_relative_to_absolute(relatives):
    """Convert relative TP percentages (by remainder) to absolute weights."""
    absolutes = []
    remaining = 1.0
    for r in relatives:
        part = round(remaining * r, 6)
        absolutes.append(part)
        remaining -= part
    return absolutes

# ==== Init client and input ====
client = get_client()
symbol = input("Symbol (e.g. BTCUSDT): ").strip().upper()
side = input("Side (Long/Short): ").capitalize()
leverage = int(input("Leverage (e.g. 10): "))
margin_usd = float(input("Margin USD (e.g. 100): "))

# ==== TP presets ====
tp_presets = [
    {
        "name": "Баланс (50/30/20)",
        "take_percents": [0.5, 0.3, 0.2],
        "platform_levels": [0.5, 0.6, 1.0]
    },
    {
        "name": "Агрессор (60/20/20)",
        "take_percents": [0.6, 0.2, 0.2],
        "platform_levels": [0.6, 0.5, 1.0]
    },
    {
        "name": "Равный (25/25/25/25)",
        "take_percents": [0.25, 0.25, 0.25, 0.25],
        "platform_levels": [0.25, 0.3333, 0.5, 1.0]
    },
    {
        "name": "Скальпер (20/20/20/20/20)",
        "take_percents": [0.2, 0.2, 0.2, 0.2, 0.2],
        "platform_levels": [0.2, 0.25, 0.3333, 0.5, 1.0]
    },
    {
        "name": "Тренд (70/20/10)",
        "take_percents": [0.7, 0.2, 0.1],
        "platform_levels": [0.7, 0.6667, 1.0]
    },
    {
        "name": "Пирамида (40/30/20/10)",
        "take_percents": [0.4, 0.3, 0.2, 0.1],
        "platform_levels": [0.4, 0.5, 0.6, 1.0]
    },
    {
        "name": "Импульс (80/15/5)",
        "take_percents": [0.8, 0.15, 0.05],
        "platform_levels": [0.8, 0.75, 1.0]
    },
    {
        "name": "Гибрид (50/25/15/10)",
        "take_percents": [0.5, 0.25, 0.15, 0.1],
        "platform_levels": [0.5, 0.6, 0.75, 1.0]
    },
    {
        "name": "Микро (20/20/20/15/15/10)",
        "take_percents": [0.2, 0.2, 0.2, 0.15, 0.15, 0.1],
        "platform_levels": [0.2, 0.25, 0.3333, 0.4286, 0.6, 1.0]
    }
]

# ==== Show and choose preset ====
print("\nChoose TP preset:\n")
for i, preset in enumerate(tp_presets):
    print(f"{i+1}. {preset['name']}")

choice = int(input("\nYour choice: ")) - 1
preset = tp_presets[choice]

tp_relative = preset["take_percents"]
platform_levels = preset["platform_levels"]

# ==== Convert relative to absolute ====
tp_percents = convert_relative_to_absolute(tp_relative) if sum(tp_relative) > 1.01 else tp_relative

# ==== Calculate TP prices from current price ====
price = get_current_price(client, symbol)
print(f"\n📈 Current price of {symbol}: {price:.2f}")

# Увеличение цены по уровням из платформенных стратегий
tp_prices = []
print("\nВведи цену для каждого тейк-профита:")
for i, percent in enumerate(tp_percents):
    tp_price = float(input(f"  TP {i+1} (доля {percent*100:.1f}%): "))
    tp_prices.append(tp_price)

# ==== Stop Loss ====
sl_price = float(input("SL Integer: "))

# ==== Place order ====
print(f"\n🛒 Placing order with:")
print(f" - TP percents: {tp_percents}")
print(f" - TP prices:   {tp_prices}")
print(f" - SL price:    {sl_price}\n")

#place_order(client, symbol, side, leverage, margin_usd, tp_prices, tp_percents, sl_price)
place_order(
    client=client,
    symbol="BTCUSDT",
    side="Buy",
    leverage=10,
    margin_usd=100,
    tp_prices=[105000, 107000, 110000],
    tp_percents=[0.5, 0.3, 0.2],
    sl_price=99000
)

