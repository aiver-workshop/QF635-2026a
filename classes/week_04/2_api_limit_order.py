"""
TOPIC: Executing and Verifying Limit Orders on Binance Testnet
REFERENCE: https://developers.binance.com/docs/derivatives/usds-margined-futures/trade/rest-api

KEY TEACHING POINTS:
1. Passive Execution: Unlike Market orders, Limit orders enter the 'Order Book'
   and only execute when the market hits your 'price'.
2. Required Parameters: Limit orders REQUIRE 'price' and 'timeInForce' (e.g., GTC - Good 'Til Cancelled).
3. Post-Only Option: Discuss 'Maker vs Taker' fees; using 'timeInForce=GTX'
   ensures the order is only accepted if it provides liquidity (Maker).
4. Order Management: Since Limit orders may not fill immediately,
   the 'status' returned is usually 'NEW', not 'FILLED'.
"""

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = 'https://testnet.binancefuture.com'


def send_limit_order(api_key: str, api_secret: str, symbol: str, quantity: float, price: float, is_buy: bool):
    """
    Creates and sends a LIMIT order to the USDⓈ-M Futures API.
    Ref: POST /fapi/v1/order
    """
    endpoint = '/fapi/v1/order'
    # TODO
    pass


if __name__ == '__main__':
    # Credentials
    API_KEY = 'CrIHchQJ5E1a5PqDkrewxyThvcNbGC1sCdDeEjwGjhvHXqWHQFJLfuoHsXkmZPvz'
    API_SECRET = 'cWWLYlLzyjUg4Rv9xxdhiXnozdCKRTCddIghS4m1DIqayJMialFpqDxgp62HPoeC'

    # Example: Place a Limit Buy for BTC at $40,000
    # Note for students: Ensure the price is realistic or far from current price to see it 'sit' in the book.
    send_limit_order(API_KEY, API_SECRET, 'BTCUSDT', 0.01, 40000.0, True)
