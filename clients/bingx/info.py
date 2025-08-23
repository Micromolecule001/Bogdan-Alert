# clients/bingx/info.py

from bingx.api import BingxAPI
from config import BINGX_API_KEY, BINGX_API_SECRET

# Инициализируем клиента один раз
client = BingxAPI(BINGX_API_KEY, BINGX_API_SECRET, timestamp="local")
def get_price(symbol: str) -> float:
    """
    Получить текущую цену торгового символа.
    """
    try:
        resp = client.get_latest_price(symbol)
        # BingxAPI возвращает число (str или float), просто приводим к float
        print(f'Price: resp: {resp}') 
        return float(resp)
    except Exception as e:
        print(f"❌ Ошибка в get_price('{symbol}'): {e}")
        raise

def get_instrument_info(symbol: str) -> dict:
    """
    Retrieve instrument information for a given symbol from BingX perpetual futures market.
    
    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC-USDT').
        
    Returns:
        dict: Instrument details (tickSize, lotSize, minQuantity, maxQuantity).
        
    Raises:
        requests.RequestException: If the API request fails.
        KeyError: If the expected data structure is not found in the response.
        ValueError: If the API returns an error.
    """
    try:
        path = "/openApi/swap/v2/quote/contracts"
        url = BASE + path
        params = {'symbol': symbol}
        
        print(f"DEBUG: Requesting URL: {url} with params: {params}")
        
        resp = requests.get(url, params=params, timeout=10)
        
        print(f"DEBUG: Response status code: {resp.status_code}")
        print(f"DEBUG: Response data: {resp.json()}")
        
        resp.raise_for_status()
        
        info = resp.json()
        
        if 'code' in info and info['code'] != 0:
            raise ValueError(f"BingX API error: {info.get('msg', 'Unknown error')}")
        
        if 'data' not in info or not info['data']:
            raise KeyError("No data found in API response")
            
        contract_info = next((item for item in info['data'] if item['symbol'] == symbol), None)
        if not contract_info:
            raise KeyError(f"No contract info found for symbol {symbol}")
        
        print(f"DEBUG: Extracted contract info: {contract_info}")
        
        return {
            'tickSize': str(10 ** -contract_info['pricePrecision']),  # Convert precision to tick size (e.g., 1 -> 0.1)
            'lotSizeStep': contract_info['size'],
            'minOrderQty': contract_info['tradeMinQuantity'],
            'maxOrderQty': contract_info.get('maxQuantity', '100')  # Default if not provided
        }
        
    except requests.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        raise
    except KeyError as e:
        print(f"❌ Data structure error: {str(e)}. Response: {info}")
        raise
    except ValueError as e:
        print(f"❌ Value error: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        raise
