def get_instrument_info(client, symbol):
    response = client.get_instruments_info(category="linear", symbol=symbol)
    if response["retCode"] == 0:
        instrument = response["result"]["list"][0]
        return {
            "tickSize": float(instrument["priceFilter"]["tickSize"]),
            "qtyStep": float(instrument["lotSizeFilter"]["qtyStep"]),
            "minOrderQty": float(instrument["lotSizeFilter"]["minOrderQty"]),
            "maxOrderQty": float(instrument["lotSizeFilter"]["maxOrderQty"])
        }
    raise Exception(f"Instrument info error: {response['retMsg']}")

def get_current_price(client, symbol):
    response = client.get_tickers(category="linear", symbol=symbol)
    if response["retCode"] == 0:
        return float(response["result"]["list"][0]["lastPrice"])
    raise Exception(f"Price error: {response['retMsg']}")
