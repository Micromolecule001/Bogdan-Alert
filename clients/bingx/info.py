import requests
from .utils import BASE

def get_price(symbol: str) -> float:
    path = "/openApi/swap/v2/market/ticker"
    resp = requests.get(BASE + path, params={'symbol': symbol})
    data = resp.json()
    print(data)
    return float(data['data']['lastPrice'])

def get_instrument_info(symbol: str) -> dict:
    path = "/openApi/swap/v2/market/contracts"
    resp = requests.get(BASE + path, params={'symbol': symbol})
    info = resp.json()
    return info['data']['contractInfoList'][0]
