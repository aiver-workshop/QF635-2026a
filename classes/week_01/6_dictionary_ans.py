"""
EXERCISE: Dictionary Order Books & Weighted Mid
Goal: Map prices to sizes and calculate a more accurate "Fair Value."
Reference: https://docs.python.org/3/howto/sorting.html
"""

bids = {}
asks = {}

# add the following price/size to bids side: (12.5, 5), (15.2, 4), (11.8, 3)
bids[12.5] = 5
bids[15.2] = 4
bids[11.8] = 3

# add the following price/size to asks side: (24.7, 6), (21.5, 5), (22.1, 1)
asks[24.7] = 6
asks[21.5] = 5
asks[22.1] = 1

# use sorted() to sort bids in descending order to print best price (15.2)
sorted_bids = sorted(bids, reverse=True)
print("best bid: ", sorted_bids[0])

# use sorted() to sort asks in ascending order to print best price (21.5)
sorted_asks = sorted(asks)
print("best ask: ", sorted_asks[0])

# compute mid
best_bid_price = sorted_bids[0]
best_ask_price = sorted_asks[0]
mid = 0.5 * (best_bid_price + best_ask_price)
print("mid: ", mid)

# compute size weighted mid
best_bid_size = bids[best_bid_price]
best_ask_size = asks[best_ask_price]

swm = ((best_bid_price * best_bid_size) + (best_ask_price * best_ask_size)) / (best_bid_size + best_ask_size)
print("size-weighted mid: ", swm)
