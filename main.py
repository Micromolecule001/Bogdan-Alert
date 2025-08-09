from config import tp_presets, client_map

def convert_relative_to_absolute(relatives):
    absolutes = []
    remaining = 1.0
    for r in relatives:
        part = round(remaining * r, 6)
        absolutes.append(part)
        remaining -= part
    return absolutes

def main():
    # ===== Выбор биржи =====
    print("Выбери биржу:")
    for i, name in enumerate(client_map.keys(), start=1):
        print(f"{i}. {name.capitalize()}")

    try:
        exchange_names = list(client_map.keys())
        raw_input = input("Введите номер биржи: ")
        choice = int(raw_input)
        if choice < 1 or choice > len(exchange_names):
            print(f"DEBUG: Invalid choice: {choice} (out of range)")
            raise IndexError("Choice out of range")
        
        selected_exchange = exchange_names[choice - 1]
        ClientClass = client_map[selected_exchange]
        client = ClientClass()
        print(f"\n✅ Биржа выбрана: {selected_exchange}")
        
    except ValueError:
        print(f"❌ Неверный ввод: введите целое число. Raw input was: '{raw_input}'")
    except IndexError:
        print(f"❌ Неверный выбор биржи: выберите число от 1 до {len(exchange_names)}.")
    except KeyError:
        print(f"❌ Ошибка: биржа '{selected_exchange}' не найдена в client_map.")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {str(e)}")

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

    tp_percents = convert_relative_to_absolute(tp_relative) if sum(tp_relative) > 1.01 else tp_relative

    # ===== Получение цены и ввод TP =====
    try:
        price = client.get_price(symbol)
        print(f"\n📈 Текущая цена {symbol}: {price:.2f}")
    except Exception as e:
        print(f"❌ Ошибка при получении цены: {e}")
        return

    tp_prices = []
    print("\nВведи цену для каждого тейк-профита:")
    for i, percent in enumerate(tp_percents):
        try:
            tp_price = float(input(f"  TP {i + 1} (доля {percent * 100:.1f}%): "))
            tp_prices.append(tp_price)
        except ValueError:
            print("❌ Неверное значение цены.")
            return

    # ===== Stop Loss =====
    try:
        sl_price = float(input("SL price: "))
    except ValueError:
        print("❌ Неверное значение SL.")
        return

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


if __name__ == "__main__":
    while True:
        main()
        again = input("\n➡️  Разместить ещё один ордер? (y/N): ").lower()
        if again != "y":
            print("👋 Выход.")
            break

