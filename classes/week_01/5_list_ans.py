"""
EXERCISE: Order Book Basics
Goal: Use lists to find the Best Bid and Best Offer (BBO) and calculate the Mid.
"""

# 1. Bid Prices (Buyers): Highest price is the "Best Bid"
bid_prices = [98, 100, 99]
bid_prices.sort(reverse=True)  # Sort descending: [100, 99, 98]

# 2. TODO: Add some Ask Prices (Sellers)
ask_prices = [102, 101, 103]

# 3. TODO: Sort Ask Prices
# Sellers want the highest price, but the "Best Offer" is the lowest one available
ask_prices.sort()  # Sort ascending: [101, 102, 103]

# 4. TODO: Get Best Bid (First element of sorted descending list)
best_bid = bid_prices[0]

# 5. TODO: Get Best Offer (First element of sorted ascending list)
best_offer = ask_prices[0]

# 6. TODO: Compute Mid from Best Bid and Offer
mid_price = (best_bid + best_offer) / 2

# Verification
print(f"Sorted Bids: {bid_prices}")
print(f"Sorted Asks: {ask_prices}")
print(f"Best Bid: {best_bid} | Best Offer: {best_offer}")
print(f"The Mid-Price is: {mid_price}")
