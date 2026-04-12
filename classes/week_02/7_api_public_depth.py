"""
TOPIC: Passing Query Parameters in REST Requests
REFERENCE: https://realpython.com

KEY TEACHING POINTS:
1. Query Parameters: Parameters are key-value pairs added to a URL (after a '?')
   to filter or specify the data requested (e.g., ?symbol=BTCUSDT).
2. The 'params' Argument: The 'requests' library allows you to pass a Python
   dictionary to 'params', which it then automatically formats into a valid URL.
3. Order Book Depth: Market 'depth' represents the supply (asks) and demand (bids).
   In professional APIs, these are usually returned as nested lists.
4. Top-of-Book: The first element in the 'bids' or 'asks' list [0] represents
    the 'Best' price currently available in the market.
"""

import requests

# Base endpoint for Binance Futures
URL = 'https://fapi.binance.com'

# Method for Market Depth (Order Book)
# https://binance-docs.github.io/apidocs/futures/en/#order-book
METHOD = '/fapi/v1/depth'

# 1. Define the parameters for the request
# We specify 'limit=5' to keep the response small and manageable
payload = {'symbol': 'BTCUSDT', 'limit': 5}

# 2. Send GET request with parameters
# The library converts this to: https://binance.com
response = requests.get(URL + METHOD, params=payload)

# 3. Parse the JSON response
order_book = response.json()

# 4. Extract Top-of-Book data and print best bid and ask prices
# Structure is: [[price, quantity], [price, quantity], ...]
# TODO

