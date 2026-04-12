"""
TOPIC: Building a Periodic Execution Loop (The "Hello World" of Algo Trading)

USER HOME DIRECTORY (~) LOCATIONS:
- Windows: C:/Users/<YourUsername>
- macOS:   /Users/<YourUsername>

KEY TEACHING POINTS:
1. The Logic Loop: Strategies often run in an infinite 'while True' loop,
   acting as the heartbeat of the trading bot.
2. The 'Flip' Logic: Using boolean toggles (is_buy = not is_buy) is a
   common way to switch between entry and exit states.
3. Exception Resilience: If one order fails due to a network glitch, the
   loop should continue rather than crashing the entire program.
4. Rate Limiting: Always include 'time.sleep()' to respect exchange API
   limits and prevent your IP from being banned.
"""

import os
import time
import hmac
import hashlib
import requests
import logging
from urllib.parse import urlencode
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- SECTION 1: SECURE CREDENTIAL LOADING ---
user_home = os.path.expanduser("~")
# Note: Ensure your file is named 'binance_keys' inside the 'vault' folder
vault_path = os.path.join(user_home, 'vault', 'binance_keys.txt')


def get_credentials():
    if os.path.exists(vault_path):
        load_dotenv(dotenv_path=vault_path)
        key = os.getenv('API_KEY')
        secret = os.getenv('API_SECRET')
        if not key or not secret:
            logging.error("Credentials missing inside the file.")
        return key, secret
    else:
        logging.error(f"Vault file not found at: {vault_path}")
        return None, None


# --- SECTION 2: ORDER EXECUTION ---
BASE_URL = 'https://testnet.binancefuture.com'


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


# --- SECTION 3: STRATEGY LOOP ---
if __name__ == '__main__':
    api_key, api_secret = get_credentials()

    if api_key and api_secret:
        is_buy = True
        logging.info("Starting Periodic Strategy...")

        try:
            # Core strategy loop
            while True:
                # 1. Execute Order
                send_market_order(api_key, api_secret, 'BTCUSDT', 0.01, is_buy)

                # 2. Wait (Teaching Point: Prevent 429 Rate Limit errors)
                logging.info("Waiting 10 seconds for next cycle...")
                time.sleep(10)

                # 3. Flip Side (Teaching Point: Simple state management)
                is_buy = not is_buy
        except KeyboardInterrupt:
            logging.info("Strategy stopped by user.")
