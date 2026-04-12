"""
TOPIC: Executing and Verifying Market Orders on Binance Testnet
REFERENCE: https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api

KEY TEACHING POINTS:
1. Automated Execution: Sending a 'POST' request to '/fapi/v1/order' immediately triggers a trade on the exchange.
2. The Signature Loop: Every private request (POST or GET) must include a fresh 'timestamp' and a unique 'signature'.
3. Order Confirmation: After a MARKET order, the 'orderId' is used to retrieve the actual 'avgPrice' (Execution Price) from the exchange.
4. Session Management: Using 'requests.Session()' is more efficient for multiple calls as it reuses the underlying TCP connection.
"""

import logging
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

# Configure logging for classroom visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = 'https://testnet.binancefuture.com'


def send_market_order(api_key: str, api_secret: str, symbol: str, quantity: float, is_buy: bool):
    """
    Creates and sends a MARKET order to the USDⓈ-M Futures API.
    Ref: POST /fapi/v1/order
    """
    endpoint = '/fapi/v1/order'

    # Required parameters for a MARKET order per documentation
    # symbol, side, type, quantity, and timestamp are mandatory.
    params = {
        "symbol": symbol.upper(),
        "side": "BUY" if is_buy else "SELL",
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": int(time.time() * 1000)
    }

    # Generate HMAC SHA256 Signature
    query_string = urlencode(params)
    signature = hmac.new(
        api_secret.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Construct final URL with signature as a query parameter
    url = f"{BASE_URL}{endpoint}?{query_string}&signature={signature}"

    # Use a Session for connection pooling (Teaching Point #4)
    session = requests.Session()
    session.headers.update({"X-MBX-APIKEY": api_key})

    try:
        # HTTP request - POST
        response = session.post(url)
        data = response.json()

        if response.status_code == 200:
            # Teaching Point #3: Extracting order confirmation details
            order_id = data.get('orderId')
            order_side = data.get('side')
            order_qty = data.get('origQty')
            order_status = data.get('status')
            logging.info(f"✅ Order Executed | ID: {order_id} | Side: {order_side} | Qty: {order_qty} | Status: {order_status}")
            return data
        else:
            logging.error(f"❌ Order Failed: {data.get('msg')} (Code: {data.get('code')})")
            return None

    except Exception as e:
        logging.error(f"📡 Network Error: {e}")
        return None


if __name__ == '__main__':
    # Students: Insert your Testnet API credentials here
    API_KEY = 'CrIHchQJ5E1a5PqDkrewxyThvcNbGC1sCdDeEjwGjhvHXqWHQFJLfuoHsXkmZPvz'
    API_SECRET = 'cWWLYlLzyjUg4Rv9xxdhiXnozdCKRTCddIghS4m1DIqayJMialFpqDxgp62HPoeC'

    # Example: Market Buy 0.01 BTCUSDT
    send_market_order(API_KEY, API_SECRET, 'BTCUSDT', 0.01, True)
