"""
TOPIC: Building a Range Trading (Mean Reversion) Strategy
REFERENCE: https://binance.com

USER HOME DIRECTORY (~) LOCATIONS:
- Windows: C:/Users/<YourUsername>
- macOS:   /Users/<YourUsername>

KEY TEACHING POINTS:
1. Market Data Integration: Using the '/fapi/v1/depth' endpoint to fetch the
   Order Book and identify current 'Best Bid' and 'Best Ask'.
2. Target Position Logic: Instead of just 'Buying' or 'Selling', we calculate
   a 'Target Position' based on price boundaries (Buy low, Sell high).
3. State Management: The 'position' variable tracks our current exposure,
   ensuring we only trade the difference (order_qty) needed to reach the target.
4. Range Boundaries: If price > Upper Bound, we assume it's overbought (Short).
   If price < Lower Bound, we assume it's oversold (Long).
"""

import logging
import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

BASE_URL = 'https://testnet.binancefuture.com'


# --- DATA STRUCTURES ---

class Tier:
    def __init__(self, price: float, size: float):
        self.price = price
        self.size = size


class OrderBook:
    def __init__(self, timestamp: float, bids: list, asks: list):
        self.timestamp = timestamp
        self.bids = bids
        self.asks = asks

    def best_bid(self): return self.bids[0].price

    def best_ask(self): return self.asks[0].price


# --- HELPERS ---

def get_credentials():
    vault_path = os.path.join(os.path.expanduser('~'), 'vault', 'binance_keys.txt')
    load_dotenv(dotenv_path=vault_path)
    return os.getenv('API_KEY'), os.getenv('API_SECRET')


def get_depth(symbol: str) -> OrderBook:
    """Fetches and parses the Order Book."""
    response = requests.get(f"{BASE_URL}/fapi/v1/depth", params={'symbol': symbol.upper(), 'limit': 5})
    data = response.json()

    bids = [Tier(float(l[0]), float(l[1])) for l in data['bids']]
    asks = [Tier(float(l[0]), float(l[1])) for l in data['asks']]
    # Use current local time if 'T' is missing from testnet response
    event_time = time.time()

    return OrderBook(event_time, bids, asks)


def send_market_order(key: str, secret: str, symbol: str, quantity: float, is_buy: bool):
    endpoint = '/fapi/v1/order'
    params = {
        "symbol": symbol.upper(),
        "side": "BUY" if is_buy else "SELL",
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": int(time.time() * 1000)
    }

    query_string = urlencode(params)
    signature = hmac.new(secret.encode("utf-8"), query_string.encode("utf-8"), hashlib.sha256).hexdigest()
    url = f"{BASE_URL}{endpoint}?{query_string}&signature={signature}"

    headers = {"X-MBX-APIKEY": key}

    try:
        with requests.Session() as session:
            response = session.post(url, headers=headers)
            data = response.json()
            if response.status_code == 200:
                logging.info(f"✅ Trade Executed: {params['side']} {quantity} {symbol}")
                return data.get('orderId')
            else:
                logging.error(f"❌ Trade Failed: {data.get('msg')}")
                return None
    except Exception as e:
        logging.error(f"📡 Connection Error: {e}")
        return None


# --- MAIN STRATEGY LOOP ---

if __name__ == '__main__':
    # Configurable Parameters
    SYMBOL = 'BTCUSDT'
    UPPER_BOUND = 73000  # Adjust based on current market
    LOWER_BOUND = 72000  # Adjust based on current market
    TARGET_SIZE = 0.01  # Quantity per trade

    api_key, api_secret = get_credentials()
    # Teaching Point: Guard Clause to prevent execution without keys
    if not api_key or not api_secret:
        logging.error("❌ CRITICAL: API credentials not found in vault. Exiting program.")
        exit(1)  # Exit with error code 1

    current_position = 0  # Simplified: assumes starting from 0

    logging.info(f"Starting Range Strategy on {SYMBOL} [{LOWER_BOUND} - {UPPER_BOUND}]")

    try:
        while True:
            # 1. Fetch Market Data
            order_book = get_depth(SYMBOL)
            bid = order_book.best_bid()
            ask = order_book.best_ask()

            # 2. Determine Target Position Logic
            if bid > UPPER_BOUND:
                target_position = -TARGET_SIZE  # Price is high, we want to be Short
            elif ask < LOWER_BOUND:
                target_position = TARGET_SIZE  # Price is low, we want to be Long
            else:
                target_position = 0  # Price is inside range, stay Neutral

            # 3. Calculate and Execute Trade
            if target_position != current_position:
                trade_qty = target_position - current_position
                is_buy = trade_qty > 0

                logging.info(f"Signal! Current Pos: {current_position} -> Target: {target_position}")

                fill = send_market_order(api_key, api_secret, SYMBOL, abs(trade_qty), is_buy)

                if fill:
                    current_position = target_position
                    logging.info(f"✅ Order Filled @ {fill}. New Position: {current_position}")

            logging.info(f"Mkt: {bid}/{ask} | Range: {LOWER_BOUND}-{UPPER_BOUND} | Pos: {current_position}")

            # 4. Throttle polling to prevent rate limiting
            time.sleep(5)  # Throttle polling to prevent rate limiting

    except KeyboardInterrupt:
        logging.info("Strategy stopped by user.")
