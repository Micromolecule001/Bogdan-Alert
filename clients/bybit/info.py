def get_price(client, symbol: str) -> float:
    response = client.get_tickers(category="linear", symbol=symbol)
    return float(response["result"]["list"][0]["lastPrice"])


def get_instrument_info(client, symbol: str) -> dict:
    response = client.get_instruments_info(category="linear", symbol=symbol)
    return response["result"]["list"][0]

