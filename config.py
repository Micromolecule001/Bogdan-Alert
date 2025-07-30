from dotenv import load_dotenv
import os

load_dotenv()

BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
BYBIT_API_SECRET = os.getenv("BYBIT_API_SECRET")

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET")

BINGX_API_KEY = os.getenv("BINANCE_API_KEY")
BINGX_API_SECRET = os.getenv("BINANCE_API_SECRET")

from clients.bybit_client import BybitClient
from clients.binance_client import BinanceClient 
from clients.bingx_client import BingXClient

client_map = {
    "bybit": BybitClient,
    "binance": BinanceClient,
    "bingx": BingXClient 
}

tp_presets = [
    {
        "name": "Баланс (50/30/20)",
        "take_percents": [0.5, 0.3, 0.2],
        "platform_levels": [0.5, 0.6, 1.0]
    },
    {
        "name": "Агрессор (60/20/20)",
        "take_percents": [0.6, 0.2, 0.2],
        "platform_levels": [0.6, 0.5, 1.0]
    },
    {
        "name": "Равный (25/25/25/25)",
        "take_percents": [0.25, 0.25, 0.25, 0.25],
        "platform_levels": [0.25, 0.3333, 0.5, 1.0]
    },
    {
        "name": "Скальпер (20/20/20/20/20)",
        "take_percents": [0.2, 0.2, 0.2, 0.2, 0.2],
        "platform_levels": [0.2, 0.25, 0.3333, 0.5, 1.0]
    },
    {
        "name": "Тренд (70/20/10)",
        "take_percents": [0.7, 0.2, 0.1],
        "platform_levels": [0.7, 0.6667, 1.0]
    },
    {
        "name": "Пирамида (40/30/20/10)",
        "take_percents": [0.4, 0.3, 0.2, 0.1],
        "platform_levels": [0.4, 0.5, 0.6, 1.0]
    },
    {
        "name": "Импульс (80/15/5)",
        "take_percents": [0.8, 0.15, 0.05],
        "platform_levels": [0.8, 0.75, 1.0] },
    {
        "name": "Гибрид (50/25/15/10)",
        "take_percents": [0.5, 0.25, 0.15, 0.1],
        "platform_levels": [0.5, 0.6, 0.75, 1.0]
    },
    {
        "name": "Микро (20/20/20/15/15/10)",
        "take_percents": [0.2, 0.2, 0.2, 0.15, 0.15, 0.1],
        "platform_levels": [0.2, 0.25, 0.3333, 0.4286, 0.6, 1.0]
    },
    {
        "name": "Двойной (50/50)",
        "take_percents": [0.5, 0.5],
        "platform_levels": [0.04, 0.12]
    },
    {
        "name": "Стандарт A (33/33/34)",
        "take_percents": [0.33, 0.33, 0.34],
        "platform_levels": [0.02, 0.05, 0.10]
    },
    {
        "name": "Стандарт B (25/25/25/25)",
        "take_percents": [0.25, 0.25, 0.25, 0.25],
        "platform_levels": [0.01, 0.02, 0.04, 0.10]
    },
    {
        "name": "Стандарт C (25/25/25/25)",
        "take_percents": [0.25, 0.25, 0.25, 0.25],
        "platform_levels": [0.02, 0.04, 0.075, 0.125]
    },
    {
        "name": "Восьмикратный (12.5% x8)",
        "take_percents": [0.125] * 8,
        "platform_levels": [0.005, 0.007, 0.013, 0.02, 0.033, 0.055, 0.088, 0.144]
    },
    {
        "name": "Тренд 2 (25/25/25/25)",
        "take_percents": [0.25, 0.25, 0.25, 0.25],
        "platform_levels": [0.015, 0.033, 0.05, 0.105]
    },
    {
        "name": "Баланс 2 (50/30/20)",
        "take_percents": [0.5, 0.3, 0.2],
        "platform_levels": [0.005, 0.01, 0.02]
    },
    {
        "name": "Скальпер 2 (20% x5)",
        "take_percents": [0.2] * 5,
        "platform_levels": [0.001, 0.002, 0.003, 0.004, 0.005]
    },
    {
        "name": "Пирамида 2 (40/30/20/10)",
        "take_percents": [0.4, 0.3, 0.2, 0.1],
        "platform_levels": [0.004, 0.008, 0.012, 0.016]
    },
    {
        "name": "Импульс 2 (80/15/5)",
        "take_percents": [0.8, 0.15, 0.05],
        "platform_levels": [0.002, 0.01, 0.03]
    },
    {
        "name": "Микро 2 (20/20/20/15/15/10)",
        "take_percents": [0.2, 0.2, 0.2, 0.15, 0.15, 0.1],
        "platform_levels": [0.0005, 0.001, 0.0015, 0.002, 0.0025, 0.003]
    },
    {
        "name": "Консервативный (60/40)",
        "take_percents": [0.6, 0.4],
        "platform_levels": [0.01, 0.02]
    },
    {
        "name": "Агрессивный (70/20/10)",
        "take_percents": [0.7, 0.2, 0.1],
        "platform_levels": [0.0025, 0.005, 0.01]
    }
]

