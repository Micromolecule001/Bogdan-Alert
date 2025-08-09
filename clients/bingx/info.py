import requests
from .utils import BASE

def get_price(symbol: str) -> float:
    """
    Retrieve the latest price for a given symbol from BingX perpetual futures market.
    
    Args:
        symbol (str): Trading pair symbol (e.g., 'BTC-USDT').
        
    Returns:
        float: The latest price of the symbol.
        
    Raises:
        requests.RequestException: If the API request fails.
        KeyError: If the expected data structure is not found in the response.
        ValueError: If the price cannot be converted to a float.
    """
    try:
        # Define the BingX API endpoint for perpetual futures ticker
        path = "/openApi/swap/v2/quote/ticker"
        url = BASE + path
        params = {'symbol': symbol}
        
        # Debug: Print the request details
        print(f"DEBUG: Requesting URL: {url} with params: {params}")
        
        # Make the API request
        resp = requests.get(url, params=params, timeout=10)
        
        # Debug: Print the response status and raw data
        print(f"DEBUG: Response status code: {resp.status_code}")
        print(f"DEBUG: Response data: {resp.json()}")
        
        # Raise an error for bad HTTP status codes
        resp.raise_for_status()
        
        # Parse the JSON response
        data = resp.json()
        
        # Check if the response contains the expected structure
        if 'code' in data and data['code'] != 0:
            raise ValueError(f"BingX API error: {data.get('msg', 'Unknown error')}")
        
        if 'data' not in data or not data['data']:
            raise KeyError("No data found in API response")
            
        # Extract the last price (corrected to access dictionary, not list)
        last_price = data['data']['lastPrice']
        
        # Debug: Print the extracted price
        print(f"DEBUG: Extracted lastPrice: {last_price}")
        
        # Convert to float and return
        return float(last_price)
        
    except requests.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        raise
    except KeyError as e:
        print(f"❌ Data structure error: {str(e)}. Response: {data}")
        raise
    except ValueError as e:
        print(f"❌ Value error: {str(e)}")
        raise
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
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
