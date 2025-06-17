def get_instrument_info(client, symbol):
    response = client.get_instruments_info(category="linear", symbol=symbol)
    return response["result"]["list"][0]

def get_current_price(client, symbol):
    response = client.get_tickers(category="linear", symbol=symbol)
    return float(response["result"]["list"][0]["lastPrice"])
