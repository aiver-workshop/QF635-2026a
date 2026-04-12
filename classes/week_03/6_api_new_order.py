"""
TOPIC: Executing and Verifying Market Orders on Binance Testnet
REFERENCE: https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api

KEY TEACHING POINTS:
1. Automated Execution: Sending a 'POST' request to '/fapi/v1/order'
   immediately triggers a trade on the exchange.
2. The Signature Loop: Every private request (POST or GET) must include
   a fresh 'timestamp' and a unique 'signature'.
3. Order Confirmation: After a MARKET order, the 'orderId' is used to
   retrieve the actual 'avgPrice' (Execution Price) from the exchange.
4. Session Management: Using 'requests.Session()' is more efficient for
   multiple calls as it reuses the underlying TCP connection.
"""
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode


def get_signature(params: dict, secret: str) -> str:
    """Helper to generate HMAC SHA256 signature."""
    query_string = urlencode(params)
    return hmac.new(
        secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


# TODO 1. Configuration (In production, use os.getenv from your vault!)
API_KEY = None
API_SECRET = None
BASE_URL = None
ORDER_PATH = None

# 2. Setup Session with persistent Headers
session = requests.Session()
session.headers.update({"X-MBX-APIKEY": API_KEY})

# TODO 3. Market BUY Order parameters ---
order_params = {}

# 4. Sign and build the full URL
sig = get_signature(order_params, API_SECRET)
full_url = f"{BASE_URL}{ORDER_PATH}?{urlencode(order_params)}&signature={sig}"

# 5. Send order request
print(f"Sending MARKET BUY for 0.01 BTC...")
response = session.post(full_url)
order_data = response.json()

# 6. Process order response
if response.status_code == 200:
    order_id = order_data['orderId']
    print(f"✅ Order Placed! ID: {order_id}")

    # --- 7. Query Order Status for Fill Price ---
    # We must wait a tiny moment or ensure the order is 'FILLED'
    time.sleep(0.5)

    status_params = {
        "symbol": "BTCUSDT",
        "orderId": order_id,
        "timestamp": int(time.time() * 1000)
    }

    status_sig = get_signature(status_params, API_SECRET)
    status_url = f"{BASE_URL}{ORDER_PATH}?{urlencode(status_params)}&signature={status_sig}"

    status_response = session.get(status_url)
    details = status_response.json()

    avg_price = details.get('avgPrice', '0.0')
    print(f"📈 Trade Execution Detail:")
    print(f"   Status: {details['status']}")
    print(f"   Avg Fill Price: ${float(avg_price):,.2f}")
else:
    print(f"❌ Order Failed: {order_data.get('msg', 'Unknown Error')}")
