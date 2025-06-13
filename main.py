from client import get_client
from order import place_order
from config import SYMBOL

def main():
    symbol = SYMBOL
    side = "Buy"
    leverage = 10
    margin = 100
    tp1 = 110000
    sl = 100000
    new_sl = 108000

    client = get_client()
    place_order(client, symbol, side, leverage, margin, tp1, sl, new_sl)

if __name__ == "__main__":
    main()
