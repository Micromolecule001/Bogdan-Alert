import time
import hmac
import hashlib
from urllib.parse import urlencode
from config import BINGX_API_KEY, BINGX_API_SECRET

__all__ = ["get_timestamp_ms", "sign_params", "build_auth_params", "round_to_step"]

def get_timestamp_ms() -> int:
    return int(time.time() * 1000)

def sign_params(params: dict, secret: str) -> str:
    sorted_params = dict(sorted(params.items()))
    query = urlencode(sorted_params)
    signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    return signature

def build_auth_params(params: dict) -> dict:
    params['timestamp'] = get_timestamp_ms()
    params['apiKey'] = BINGX_API_KEY
    params['signature'] = sign_params(params, BINGX_API_SECRET)
    return params

def round_to_step(value, step):
    return round(round(value / step) * step, 8)
