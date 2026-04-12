"""
TOPIC: Programmatic Order Cancellation on Binance Testnet
REFERENCE: https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api/Cancel-Order

KEY TEACHING POINTS:
1. HTTP Verb Change: Canceling an order requires a 'DELETE' request,
   differentiating it from placing (POST) or querying (GET).
2. Atomic Operation: Once a 'DELETE' request is processed, the order
   is removed from the matching engine (unless already filled).
3. Error Handling: Attempting to cancel an order that is already 'FILLED'
   or 'CANCELED' will return a 400 error (e.g., -2011 "Unknown order").
4. Bulk Cancellation: While this script handles one order, the API also
   supports 'DELETE /fapi/v1/allOpenOrders' for emergency stops.
"""

import logging


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = 'https://testnet.binancefuture.com'


def cancel_order(api_key: str, api_secret: str, symbol: str, order_id: int):
    """
    Cancels an active open order on the USDⓈ-M Futures API.
    Ref: DELETE /fapi/v1/order
    """
    endpoint = '/fapi/v1/order'

    # TODO
    pass


if __name__ == '__main__':
    API_KEY = 'CrIHchQJ5E1a5PqDkrewxyThvcNbGC1sCdDeEjwGjhvHXqWHQFJLfuoHsXkmZPvz'
    API_SECRET = 'cWWLYlLzyjUg4Rv9xxdhiXnozdCKRTCddIghS4m1DIqayJMialFpqDxgp62HPoeC'

    # STUDENT CHALLENGE:
    # 1. Use your Limit Order script to place an order at $10,000 (well below market).
    # 2. Capture the 'orderId'.
    # 3. Run this script to cancel it.
    # 4. Try running this script a SECOND time on the same ID to observe the error response.

    target_id = 13029809349  # Replace with an active Order ID
    cancel_order(API_KEY, API_SECRET, 'BTCUSDT', target_id)
