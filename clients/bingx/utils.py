# .utils.py
import math
import time
import hmac
import hashlib
import json

BASE = "https://open-api.bingx.com"

def map_side_for_bingx(side: str) -> str:
    """Конвертация BUY/SELL/LONG/SHORT в LONG/SHORT для BingX."""
    side = side.strip().lower()
    side_map = {
        "buy": "LONG",
        "long": "LONG",
        "sell": "SHORT",
        "short": "SHORT"
    }
    if side not in side_map:
        raise ValueError(f"Invalid side '{side}' — use buy/sell or long/short")
    return side_map[side]

def build_auth_params(payload: dict, api_secret: str) -> dict:
    """
    Build authenticated parameters for BingX API requests.
    
    Args:
        payload (dict): The original payload dictionary.
        api_secret (str): The API secret key for signing.
        
    Returns:
        dict: The payload with timestamp and signature added.
    """
    # Convert numbers to str with :g to remove unnecessary decimals
    for k, v in payload.items():
        if isinstance(v, float) or isinstance(v, int):
            payload[k] = '{:g}'.format(v)
        if isinstance(v, (dict, list)):
            # For nested, we'll handle in the place_order
            pass
    
    # Stringify nested structures (dicts/lists)
    for k, v in payload.items():
        if isinstance(v, (dict, list)):
            payload[k] = json.dumps(v, separators=(',', ':'))
    
    # Add timestamp
    payload['timestamp'] = str(int(time.time() * 1000))
    
    # Sort keys and build query string
    sorted_keys = sorted(payload.keys())
    query_string = '&'.join(f"{k}={payload[k]}" for k in sorted_keys)
    
    # Generate signature (hex digest)
    signature = hmac.new(
        api_secret.encode('utf-8'), 
        query_string.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()

    print('Signature: \n\n' + signature)
    
    # Add signature to payload
    payload['signature'] = signature

    print(payload)

    return payload

def round_to_step(value: float, step: float) -> float:
    if step <= 0:
        return float(value)
    return math.floor(float(value) / step + 1e-12) * step

def normalize_symbol(symbol: str) -> str:
    """BTCUSDT -> BTC-USDT; уже корректный формат оставляем как есть."""
    s = symbol.strip().upper()
    if "-" in s:
        return s
    if s.endswith("USDT") and len(s) > 5:
        return f"{s[:-4]}-USDT"
    return s  # пусть будет так, напечатаем в DEBUG что не уверены

