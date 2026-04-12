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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = 'https://testnet.binancefuture.com'


def get_order_status(api_key: str, api_secret: str, symbol: str, order_id: int):
    """
    Check the current state of a specific order.
    Ref: GET /fapi/v1/order
    """
    endpoint = '/fapi/v1/order'

    # TODO
    pass


if __name__ == '__main__':
    API_KEY = 'CrIHchQJ5E1a5PqDkrewxyThvcNbGC1sCdDeEjwGjhvHXqWHQFJLfuoHsXkmZPvz'
    API_SECRET = 'cWWLYlLzyjUg4Rv9xxdhiXnozdCKRTCddIghS4m1DIqayJMialFpqDxgp62HPoeC'

    # STUDENT EXERCISE:
    # 1. Place a LIMIT order far from the market price.
    # 2. Capture the 'orderId' from that response.
    # 3. Use this script to verify the status is 'NEW'.
    # 4. Cancel the order on the web UI and run this script again to see it change to 'CANCELED'.

    target_id = 13029802688  # Replace with a real order ID from your previous script
    get_order_status(API_KEY, API_SECRET, 'BTCUSDT', target_id)
