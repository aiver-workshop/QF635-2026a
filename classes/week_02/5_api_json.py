"""
TOPIC: JSON Data Extraction & VWAP Mid-Price Calculation
REFERENCE: https://realpython.com

KEY TEACHING POINTS:
1. JSON Deserialization: Converting a raw string into a Python dictionary
   using 'json.loads()'.
2. Nested List Indexing: Accessing specific data points within nested
   lists (e.g., data['bids'][0][0] for the best bid price).
3. Type Casting: Converting JSON string values into floats to perform
   mathematical operations.
4. VWAP Mid-Price: Calculating a fair value that accounts for the
   liquidity (volume) available at the bid and ask.
"""

import json

# Simulated JSON response for Apple (AAPL)
# Format: [Price, Size]
json_data = """
{
    "symbol": "AAPL",
    "bids": [["185.50", "500"]],
    "asks": [["185.70", "1500"]]
}
"""

# TODO 1: Parse the JSON string into a dictionary
# data =

# TODO 2: Extract Apple bid/ask prices and sizes as floats
# Note: [0][0] is Price, [0][1] is Size
# b_price =
# b_size  =
# a_price =
# a_size  =

# TODO 3: Calculate the Standard Mid
# standard_mid =

# TODO 4: Calculate the VWAP (Volume-Weighted) Mid
# Formula: ((Bid_Price * Bid_Size) + (Ask_Price * Ask_Size)) / (Total_Size)
# vwap_mid =

# TODO 5: Print the results
# print(f"--- {data['symbol']} Market Data ---")
# print(f"Standard Mid: {standard_mid}")
# print(f"VWAP Mid:     {vwap_mid}")
