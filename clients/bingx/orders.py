# orders.py
import requests
from .utils import BASE, build_auth_params, round_to_step
from .info import get_price, get_instrument_info
from config import BINGX_API_KEY, BINGX_API_SECRET

def place_order(symbol: str, side: str, leverage: int, margin_usd: float, tp_prices: list, tp_percents: list, sl_price: float):
    try:
        instrument = get_instrument_info(symbol)
        print(f"DEBUG: Instrument info: {instrument}")
        
        tick = float(instrument['tickSize'])
        step = float(instrument['lotSizeStep'])
        min_qty = float(instrument['minOrderQty'])
        max_qty = float(instrument['maxOrderQty'])
        qty_precision = instrument['quantityPrecision'] if 'quantityPrecision' in instrument else 4  # Default to 4
        price_precision = instrument['pricePrecision'] if 'pricePrecision' in instrument else 1  # Default to 1
        
        price = get_price(symbol)
        print(f"DEBUG: Current price: {price}")
        
        qty = (margin_usd * leverage) / price
        qty = round_to_step(qty, step)
        print(f"DEBUG: Calculated total quantity: {qty} (min: {min_qty}, max: {max_qty})")
        
        if qty < min_qty or qty > max_qty:
            raise ValueError(f"Quantity {qty} out of bounds (min: {min_qty}, max: {max_qty})")
        
        if abs(sum(tp_percents) - 1.0) > 0.001:
            raise ValueError(f"Take-profit percentages must sum to 1.0, got {sum(tp_percents)}")
        
        if len(tp_prices) != len(tp_percents):
            raise ValueError(f"Number of TP prices ({len(tp_prices)}) must match TP percents ({len(tp_percents)})")
        
        # Determine side and positionSide
        if side == 'Long':
            market_side = 'BUY'
            position_side = 'LONG'
            tp_side = 'SELL'
        elif side == 'Short':
            market_side = 'SELL'
            position_side = 'SHORT'
            tp_side = 'BUY'
        else:
            raise ValueError(f"Invalid side: {side}. Must be 'Long' or 'Short'.")
        
        # Market order payload
        market_payload = {
            'symbol': symbol,
            'side': market_side,
            'positionSide': position_side,
            'type': 'MARKET',
            'quantity': float(f"{qty:.{qty_precision}f}")  # Format to precision, back to float
        }
        
        if sl_price:
            sl_stop_price = float(f"{sl_price:.{price_precision}f}")  # Format to precision
            market_payload['stopLoss'] = {'type': 'STOP_MARKET', 'stopPrice': int(sl_stop_price) if sl_stop_price.is_integer() else sl_stop_price}
        
        print(f"DEBUG: Market order payload: {market_payload}")
        
        # Build authenticated params
        params = build_auth_params(market_payload.copy(), BINGX_API_SECRET)
        headers = {'X-BX-APIKEY': BINGX_API_KEY}
        
        # Place market order
        path = "/openApi/swap/v2/trade/order"
        url = BASE + path
        print(f"DEBUG: Requesting market order URL: {url} with params: {params}")
        
        response = requests.post(url, params=params, headers=headers, timeout=10)
        print(f"DEBUG: Market order response status code: {response.status_code}")
        print(f"DEBUG: Market order response data: {response.json()}")
        
        result = response.json()
        if result.get('code') != 0:
            raise ValueError(f"Market order failed: {result.get('msg', 'Unknown error')}")
        
        if 'data' not in result:
            raise KeyError("No data field in market order response")
        
        market_order = result['data']
        
        # Place TP limit orders
        tp_orders = []
        for i, (tp_price, tp_percent) in enumerate(zip(tp_prices, tp_percents)):
            tp_qty = round_to_step(qty * tp_percent, step)
            tp_qty = float(f"{tp_qty:.{qty_precision}f}")
            if tp_qty < min_qty:
                print(f"DEBUG: Skipping TP {i+1}: Quantity {tp_qty} below min {min_qty}")
                continue
            
            tp_stop_price = float(f"{tp_price:.{price_precision}f}")
            tp_payload = {
                'symbol': symbol,
                'side': tp_side,
                'positionSide': position_side,
                'type': 'LIMIT',
                'quantity': tp_qty,
                'price': int(tp_stop_price) if tp_stop_price.is_integer() else tp_stop_price
            }
            
            print(f"DEBUG: TP {i+1} order payload: {tp_payload}")
            
            params = build_auth_params(tp_payload.copy(), BINGX_API_SECRET)
            response = requests.post(url, params=params, headers=headers, timeout=10)
            print(f"DEBUG: TP {i+1} order response status code: {response.status_code}")
            print(f"DEBUG: TP {i+1} order response data: {response.json()}")
            
            result = response.json()
            if result.get('code') != 0:
                print(f"❌ TP {i+1} order failed: {result.get('msg', 'Unknown error')}")
                continue
            
            if 'data' not in result:
                print(f"❌ TP {i+1} order response missing data field")
                continue
            
            tp_orders.append(result['data'])
        
        return {'market_order': market_order, 'tp_orders': tp_orders, 'qty': qty}
        
    except requests.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        raise
    except KeyError as e:
        print(f"❌ Data structure error: {str(e)}")
        raise
    except ValueError as e:
        print(f"❌ Value error: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        raise
