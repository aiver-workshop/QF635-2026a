"""
TOPIC: Building a Real-Time OrderBook Monitor
REFERENCE: https://realpython.com

KEY TEACHING POINTS:
1. Objectification: Converting raw API JSON into custom 'Tier' and 'OrderBook'
   objects allows for cleaner and more descriptive code.
2. The Factory Pattern: The 'parse' function encapsulates the complexity of
   looping through nested JSON and performing type casting (string -> float).
3. Exchange Time vs. Local Time: We use the exchange's 'event time' (T) to
   ensure our data reflects exactly when the market snapshot was taken.
4. Robustness: Including a 'try-except' block prevents the script from
   crashing during minor internet interruptions.
"""

import time
import logging
import requests
from datetime import datetime

# Standard logging configuration
logging.basicConfig(
    format='%(asctime)s [%(levelname)-5.5s]  %(message)s',
    level=logging.INFO
)


class Tier:
    """Represents a single price-size level."""

    def __init__(self, price: float, size: float):
        self.price = price
        self.size = size


class OrderBook:
    """Represents a snapshot of the market at a specific time."""

    def __init__(self, timestamp: float, bids: list[Tier], asks: list[Tier]):
        self.timestamp = timestamp
        self.bids = bids
        self.asks = asks

    def best_bid(self) -> float:
        return self.bids[0].price if self.bids else 0.0

    def best_ask(self) -> float:
        return self.asks[0].price if self.asks else 0.0


def parse_exchange_data(json_data: dict) -> OrderBook:
    """Factory function to convert Binance JSON to an OrderBook object."""

    # Process Bids and Asks using list comprehensions for cleaner code
    bids = [Tier(float(l[0]), float(l[1])) for l in json_data['bids']]
    asks = [Tier(float(l[0]), float(l[1])) for l in json_data['asks']]

    # 'T' is the transaction time in milliseconds; convert to seconds
    event_time = float(json_data['T']) / 1000
    return OrderBook(event_time, bids, asks)


if __name__ == '__main__':
    symbol = "BTCUSDT"
    endpoint = 'https://fapi.binance.com/fapi/v1/depth'

    logging.info(f"Starting OrderBook monitor for {symbol}...")

    try:
        while True:
            try:
                # 1. Fetch Market Data
                response = requests.get(endpoint, params={'symbol': symbol, 'limit': 10})
                response.raise_for_status()

                # 2. Convert to Objects
                ob = parse_exchange_data(response.json())

                # 3. Analyze and Log
                # Using fromtimestamp to show the Exchange's time, not local time
                ex_time = datetime.fromtimestamp(ob.timestamp).strftime('%H:%M:%S.%f')[:-3]
                logging.info(f"[{ex_time}] Bid: {ob.best_bid():.2f} | Ask: {ob.best_ask():.2f}")

            except Exception as e:
                logging.error(f"Iteration failed: {e}")

            # 4. Wait for next poll
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Monitor stopped by user.")
