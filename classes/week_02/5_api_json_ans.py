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

# 1. Convert JSON string to Dictionary
data = json.loads(json_data)

# 2. Extract nested values and cast to float
# bids[0] accesses the first pair, [0] is the price, [1] is the size
b_price = float(data['bids'][0][0])
b_size  = float(data['bids'][0][1])

a_price = float(data['asks'][0][0])
a_size  = float(data['asks'][0][1])

# 3. Standard Mid (Simple Average)
standard_mid = (b_price + a_price) / 2

# 4. Volume-Weighted Average Mid (VWAP Mid)
total_size = b_size + a_size
vwap_mid = ((b_price * b_size) + (a_price * a_size)) / total_size

# 5. Output
print(f"--- {data['symbol']} Price Discovery ---")
print(f"Standard Mid: {standard_mid:.2f}")
print(f"VWAP Mid:     {vwap_mid:.4f}")

# 6. Teaching Insight:
# Since there is 3x more size at the Ask (1500 vs 500),
# the VWAP Mid leans significantly closer to the Ask price.

