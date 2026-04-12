"""
TOPIC: Building Real-Time Applications via Polling
REFERENCE: https://realpython.com

KEY TEACHING POINTS:
1. Polling: A strategy where the client repeatedly "asks" the server for
   updates. This is the simplest way to simulate a real-time data feed.
2. Latency & Sleep: Using 'time.sleep()' is mandatory in polling loops to
   prevent being "IP Banned" or Rate-Limited by the exchange (429 Error).
3. Modularity: Encapsulating the API call into a function ('get_order_book')
   makes the code reusable and the main loop much cleaner.
4. Error Handling: In a live loop, the network will eventually fail. Using
   'try-except' blocks ensures one small glitch doesn't crash your whole bot.
"""

import requests
import time
import logging

# Configure logging to include timestamps for market data tracking
logging.basicConfig(
    format='%(asctime)s [%(levelname)-5.5s]  %(message)s',
    level=logging.INFO
)

# Binance API Constants
BASE_URL = 'https://fapi.binance.com'
DEPTH_METHOD = '/fapi/v1/depth'


def get_best_prices(symbol: str):
    """Fetches the top-of-book prices for a given symbol."""
    try:
        # We only need the top row, so we set limit=5 to save bandwidth
        response = requests.get(
            BASE_URL + DEPTH_METHOD,
            params={'symbol': symbol, 'limit': 5},
            timeout=5  # Don't wait forever if the internet is slow
        )

        # Raise an exception for bad status codes (4xx, 5xx)
        response.raise_for_status()

        data = response.json()

        # Binance depth returns: {"bids": [[price, qty], ...], "asks": [...]}
        best_bid = data['bids'][0][0]
        best_ask = data['asks'][0][0]

        return best_bid, best_ask

    except Exception as e:
        logging.error(f"Network Error: {e}")
        return None, None


# Entry point for the Polling Loop
if __name__ == '__main__':
    ticker = "BTCUSDT"
    logging.info(f"Starting real-time monitor for {ticker}...")

    try:
        while True:
            bid, ask = get_best_prices(ticker)

            if bid and ask:
                logging.info(f"{ticker} | Best Bid: {bid} | Best Ask: {ask}")

            # Poll every 2 seconds (30 requests per minute)
            time.sleep(2)

    except KeyboardInterrupt:
        logging.info("Monitor stopped by user.")
