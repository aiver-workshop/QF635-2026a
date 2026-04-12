"""
TOPIC: Querying Order Status and Execution Details
REFERENCE: https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Query-Order

KEY TEACHING POINTS:
1. Polling vs. WebSockets: While WebSockets are for real-time data, 'GET'
   requests to '/fapi/v1/order' are used to poll for specific order updates.
2. The 'status' Lifecycle: An order moves from 'NEW' to 'PARTIALLY_FILLED',
   'FILLED', 'CANCELED', or 'EXPIRED'.
3. Identification: You can query an order using either the 'orderId'
   (Exchange assigned) or 'origClientOrderId' (User assigned).
4. Data Integrity: Verifying 'executedQty' and 'avgPrice' ensures your
   local database matches the exchange's source of truth.
"""

import logging
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = 'https://testnet.binancefuture.com'


def get_order_status(api_key: str, api_secret: str, symbol: str, order_id: int):
    """
    Check the current state of a specific order.
    Ref: GET /fapi/v1/order
    """
    endpoint = '/fapi/v1/order'

    # Use GET method params
    params = {
        "symbol": symbol.upper(),
        "orderId": order_id,
        "timestamp": int(time.time() * 1000)
    }

    query_string = urlencode(params)
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    url = f"{BASE_URL}{endpoint}?{query_string}&signature={signature}"
    headers = {"X-MBX-APIKEY": api_key}

    session = requests.Session()
    try:
        # Note: This is a GET request, not a POST
        response = session.get(url, headers=headers)
        data = response.json()

        if response.status_code == 200:
            status = data.get('status')
            executed_qty = data.get('executedQty')
            executed_avg_price = data.get("avgPrice")
            logging.info(f"🔍 Status for Order {order_id}: {status} | Filled: {executed_qty} | AvgPrice: {executed_avg_price}")
            return data
        else:
            logging.error(f"❌ Query Failed: {data.get('msg')}")
            return None

    except Exception as e:
        logging.error(f"📡 Network Error: {e}")
        return None


if __name__ == '__main__':
    API_KEY = 'CrIHchQJ5E1a5PqDkrewxyThvcNbGC1sCdDeEjwGjhvHXqWHQFJLfuoHsXkmZPvz'
    API_SECRET = 'cWWLYlLzyjUg4Rv9xxdhiXnozdCKRTCddIghS4m1DIqayJMialFpqDxgp62HPoeC'

    # STUDENT EXERCISE:
    # 1. Place a LIMIT order far from the market price.
    # 2. Capture the 'orderId' from that response.
    # 3. Use this script to verify the status is 'NEW'.
    # 4. Cancel the order on the web UI and run this script again to see it change to 'CANCELED'.

    target_id = 13029809349  # Replace with a real order ID from your previous script
    get_order_status(API_KEY, API_SECRET, 'BTCUSDT', target_id)
