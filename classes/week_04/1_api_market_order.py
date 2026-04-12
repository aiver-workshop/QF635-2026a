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

# Configure logging for classroom visibility
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = 'https://testnet.binancefuture.com'


def send_market_order(api_key: str, api_secret: str, symbol: str, quantity: float, is_buy: bool):
    """
    Creates and sends a MARKET order to the USDⓈ-M Futures API.
    Ref: POST /fapi/v1/order
    """
    # TODO
    pass


if __name__ == '__main__':
    # Students: Insert your Testnet API credentials here
    API_KEY = 'YOUR_API_KEY'
    API_SECRET = 'YOUR_API_SECRET'

    # Example: Market Buy 0.01 BTCUSDT
    send_market_order(API_KEY, API_SECRET, 'BTCUSDT', 0.01, False)