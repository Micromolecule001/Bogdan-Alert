# clients/bingx/orders.py

import json
from typing import Optional, Literal
from bingx.api import BingxAPI
from config import BINGX_API_KEY, BINGX_API_SECRET
from .utils import normalize_symbol, round_to_step, map_side_for_bingx from .info import get_price as _get_price

def _fetch_precisions(client: BingxAPI, symbol: str):
    """
    Пытаемся добыть шаги/точности из API.
    Возвращаем: (price_tick, qty_step, min_qty)
    Если не получилось — ставим дефолты и печатаем предупреждение.
    """
    price_tick = 0.01
    qty_step = 0.001
    min_qty = 0.0

    print(f"\nBlacnce: ", client.get_perpetual_balance())

    try:
        t = client.get_tiker(symbol)
        if isinstance(t, list) and t:
            t = t[0]
        if isinstance(t, dict):
            pp = t.get("pricePrecision") or t.get("price_precision") or t.get("price_tick") or None
            qp = t.get("quantityPrecision") or t.get("quantity_precision") or t.get("qty_step") or None
            mn = t.get("minQty") or t.get("min_quantity") or t.get("minOrderQty") or 0.0

            if isinstance(pp, int):
                price_tick = 10 ** (-pp)
            elif isinstance(pp, (float, str)) and float(pp) > 0:
                price_tick = float(pp)

            if isinstance(qp, int):
                qty_step = 10 ** (-qp)
            elif isinstance(qp, (float, str)) and float(qp) > 0:
                qty_step = float(qp)

            if isinstance(mn, (float, int, str)):
                min_qty = float(mn)
    except Exception:
        pass

    # пробуем get_all_contracts как fallback
    try:
        contracts = client.get_all_contracts()
        if isinstance(contracts, list):
            sym = symbol.replace("-", "")
            for c in contracts:
                # ищем по нескольким ключам
                code = c.get("symbol") or c.get("pair") or c.get("contractCode") or ""
                code = str(code).replace("-", "").upper()
                if code == sym:
                    # разные варианты ключей
                    pp = c.get("pricePrecision") or c.get("price_tick") or c.get("tickSize")
                    qp = c.get("quantityPrecision") or c.get("qty_step") or c.get("stepSize")
                    mn = c.get("minQty") or c.get("minOrderQty") or 0.0

                    if isinstance(pp, int):
                        price_tick = 10 ** (-pp)
                    elif isinstance(pp, (float, str)) and float(pp) > 0:
                        price_tick = float(pp)
                    if isinstance(qp, int):
                        qty_step = 10 ** (-qp)
                    elif isinstance(qp, (float, str)) and float(qp) > 0:
                        qty_step = float(qp)
                    if isinstance(mn, (float, int, str)):
                        min_qty = float(mn)
                    break
    except Exception:
        pass

    print(f'price_tick: {price_tick}, qty_step: {qty_step}, min_qty: {min_qty}') 

    return float(price_tick), float(qty_step), float(min_qty)


def _debug_dump(title: str, mapping: dict):
    print(f"\n=== {title} ===")
    for k, v in mapping.items():
        print(f"{k:<18} | type={type(v).__name__:<10} | value={v}")
    print("=" * 52 + "\n")


def place_order(
    symbol: str,
    side: str,                     # "Long"/"Short" (любой регистр)
    leverage: int,
    margin_usd: float,
    tp_prices: list,
    tp_percents: list,
    sl_price: float,
    *,
    test: bool = False,            # ТЕСТОВЫЙ режим (через /test endpoint)
    entry_type: Literal["market", "limit"] = "market",
    entry_price: Optional[float] = None,  # для limit-входа
    time_in_force: str = "GTC",
    working_type: str = "MARK_PRICE",
):
    """
    Универсальная постановка входа + SL + N TP на BingX Perp v2.

    ⚙️ Поведение по умолчанию:
      - вход MARKET
      - SL через TRIGGER_MARKET
      - все TP — отдельными close_limit_order
      - без изменения вызова из main.py (доп.параметры опциональны)
    """

    # --- Нормализация входных данных
    symbol = normalize_symbol(symbol)
    position_side = map_side_for_bingx(side)  # "LONG"/"SHORT"

    print(f'\n position_side: LONG/SHORT -?> {position_side}')

    if position_side not in ("LONG", "SHORT"):
        raise ValueError("side must be LONG/SHORT (или Long/Short)")

    # --- Проверки TP
    if abs(sum(tp_percents) - 1.0) > 1e-6:
        raise ValueError("TP percents must sum to 1.0")
    if len(tp_prices) != len(tp_percents):
        raise ValueError("TP prices & percents length mismatch")
    if entry_type == "limit" and (entry_price is None or float(entry_price) <= 0):
        raise ValueError("entry_type='limit' требует entry_price > 0")

    # --- Инициализация клиента и актуальной цены
    client = BingxAPI(BINGX_API_KEY, BINGX_API_SECRET, timestamp="local")
    price = float(_get_price(symbol))
    notional = float(margin_usd) * int(leverage)
    quantity_raw = notional / price

    # --- Добываем шаги и округляем всё как нужно
    tick, step, min_qty = _fetch_precisions(client, symbol)
    qty = round_to_step(quantity_raw, step)
    sl_price = round_to_step(float(sl_price), tick)

    # Приводим TP-цены и вычисляем долевые объёмы
    tp_prices = [round_to_step(float(p), tick) for p in tp_prices]
    tp_qtys = []
    remaining = qty
    for i, pct in enumerate(tp_percents):
        part = round_to_step(qty * float(pct), step)
        # чтобы из-за округления суммарный объём совпал — остаток кидаем в последний TP
        if i == len(tp_percents) - 1:
            part = round_to_step(remaining, step)
        tp_qtys.append(part)
        remaining = max(0.0, round(float(remaining - part), 12))

    # min qty проверка
    if min_qty > 0 and qty < min_qty:
        raise ValueError(f"Calculated qty {qty} is below min {min_qty}")

    # --- Отладочный вывод
    _debug_dump(
        "[DEBUG] place_order input",
        dict(
            symbol=symbol,
            raw_side=side,
            position_side=position_side,
            leverage=leverage,
            margin_usd=margin_usd,
            current_price=price,
            notional=notional,
            quantity_raw=quantity_raw,
            qty=qty,
            tick=tick,
            step=step,
            min_qty=min_qty,
            entry_type=entry_type,
            entry_price=entry_price,
            time_in_force=time_in_force,
            working_type=working_type,
            tp_prices=tp_prices,
            tp_percents=tp_percents,
            tp_qtys=tp_qtys,
            sl_price=sl_price,
            test=test,
        )
    )

    # --- Выставляем плечо (на всякий случай — для обеих сторон)
    try:
        client.set_levarage(symbol, "LONG", leverage)
        client.set_levarage(symbol, "SHORT", leverage)
    except Exception as e:
        print(f"⚠️  set_leverage failed (ignored): {e}")

    # --- Решаем, как входить
    entry_order_resp = None
    if test:
        # тестовый вход
        decision = "BUY" if position_side == "LONG" else "SELL"
        if entry_type == "market":
            entry_order_resp = client.place_test_order(
                trade_type="MARKET",
                pair=symbol,
                desicion=decision,
                position_side=position_side,
                price="NULL",
                volume=qty,
                stop_price="NULL",
                priceRate="NULL",
                sl="NULL",
                tp="NULL",
                working_type=working_type,
                client_order_id="NULL",
                time_in_force=time_in_force,
            )
        else:
            entry_order_resp = client.place_test_order(
                trade_type="LIMIT",
                pair=symbol,
                desicion=decision,
                position_side=position_side,
                price=str(round_to_step(float(entry_price), tick)),
                volume=qty,
                stop_price="NULL",
                priceRate="NULL",
                sl="NULL",
                tp="NULL",
                working_type=working_type,
                client_order_id="NULL",
                time_in_force=time_in_force,
            )
    else:
        # боевой вход
        if entry_type == "market":
            entry_order_resp = client.open_market_order(
                pair=symbol,
                position_side=position_side,
                volume=qty,
                sl="NULL",
                tp="NULL",
                client_order_id="NULL",
            )
        else:
            entry_order_resp = client.open_limit_order(
                pair=symbol,
                position_side=position_side,
                price=str(round_to_step(float(entry_price), tick)) if entry_price else "BBO",
                volume=qty,
                sl="NULL",
                tp="NULL",
                client_order_id="NULL",
            )

    print("DEBUG: Entry order response:", json.dumps(entry_order_resp, indent=2, ensure_ascii=False))

    # 52

    # --- Ставим стоп-лосс отдельным TRIGGER_MARKET
    sl_decision = "SELL" if position_side == "LONG" else "BUY"
    if test:
        sl_resp = client.place_test_order
            trigger_price_type=working_type,
            client_order_id="NULL",
            time_in_force=time_in_force,
            tp="NULL",
            sl="NULL",
        )
    print("DEBUG: SL order response:", json.dumps(sl_resp, indent=2, ensure_ascii=False))

    # --- Ставим все TP как close_limit_order
    # Для LONG TP-цены должны быть ВЫШЕ текущей; для SHORT — НИЖЕ. Иначе предупреждаем и пропускаем.
    tp_responses = []
    for i, (tp_p, tp_q) in enumerate(zip(tp_prices, tp_qtys), start=1):
        if tp_q <= 0:
            print(f"⚠️  TP{i}: qty {tp_q} <= 0 — пропуск")
            continue

        invalid = (
            (position_side == "LONG" and tp_p <= price) or
            (position_side == "SHORT" and tp_p >= price)
        )
        if invalid:
            print(f"⚠️  TP{i}: {tp_p} «неправильная сторона» относительно текущей {price} — пропуск")
            continue

        if test:
            # тестовый close-лимит «симулируем» обычным LIMIT с противоположным решением
            tp_decision = "SELL" if position_side == "LONG" else "BUY"
            tp_resp = client.place_test_order(
                trade_type="LIMIT",
                pair=symbol,
                desicion=tp_decision,
                position_side=position_side,
                price=str(tp_p),
                volume=tp_q,
                stop_price="NULL",
                priceRate="NULL",
                sl="NULL",
                tp="NULL",
                working_type=working_type,
                client_order_id="NULL",
                time_in_force="GTC",
            )
        else:
            tp_resp = client.close_limit_order(
                pair=symbol,
                position_side=position_side,
                price=str(tp_p),
                volume=tp_q,
                client_order_id="NULL",
            )
        print(f"DEBUG: TP{i} response:", json.dumps(tp_resp, indent=2, ensure_ascii=False))
        tp_responses.append(tp_resp)


    return {
        "entry_order": entry_order_resp,
        "sl_order": sl_resp,
        "tp_orders": len(tp_responses),
        "tp_order_responses": tp_responses,
    }

