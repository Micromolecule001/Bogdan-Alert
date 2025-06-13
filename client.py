from pybit.unified_trading import HTTP
from config import API_KEY, API_SECRET

def get_client():
    return HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET, demo=True)
