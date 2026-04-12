"""
TOPIC: Interacting with RESTful APIs via HTTP
REFERENCE: https://realpython.com/python-requests/

KEY TEACHING POINTS:
1. REST Architecture: APIs act as a bridge between your script (Client) and
   the Exchange (Server). We use HTTP methods to define our intent.
2. GET Method: The primary way to retrieve data without modifying anything.
3. JSON Data: Most modern APIs return data as a JSON string, which Python
   easily converts into a dictionary or list using '.json()'.
4. API Endpoints: A complete request is formed by combining a Base URL
   (the server address) and a Method Path (the specific data folder).
5. Data Extraction: Real-world APIs return nested structures. Using loops
   is essential to parse through lists of symbols and their attributes.
"""

import requests

# Base endpoint for Binance Futures
URL = 'https://fapi.binance.com'

# Specific method for Exchange Information (Instrument Metadata)
METHOD = '/fapi/v1/exchangeInfo'

# 1. Send HTTP GET request
# This is like typing the URL into your browser and hitting 'Enter'
response = requests.get(URL + METHOD)

# 2. Check for success (Optional but recommended)
if response.status_code == 200:
    # 3. Convert the raw text response to a Python Dictionary
    exchange_info = response.json()

    # 4. Iterate through the symbols to extract specific instrument data
    # Note: 'symbols' is a list of dictionaries inside the main dictionary
    for symbol_data in exchange_info['symbols']:
        symbol = symbol_data['symbol']
        status = symbol_data['status']
        price_p = symbol_data['pricePrecision']
        qty_p = symbol_data['quantityPrecision']

        # Using f-string for modern, readable output
        print(f"{symbol:10} | Status: {status:10} | Price Prec: {price_p} | Qty Prec: {qty_p}")
else:
    print(f"Failed to connect. Status Code: {response.status_code}")


