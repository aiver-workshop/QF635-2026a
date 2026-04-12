"""
TOPIC: Domain Modeling with Classes
REFERENCE: https://realpython.com

KEY TEACHING POINTS:
1. Custom Types: We created a 'Tier' class to represent a single row in
   an order book. It holds price, size, and a unique quote ID.
2. Collections of Objects: 'bids' and 'asks' are now lists of objects
   rather than just lists of numbers.
3. Readability: Accessing 'bids[0].price' is more intuitive than 'bids[0][0]',
   reducing bugs in complex trading logic.
4. Optional Attributes: Using 'None' as a default for 'quote_id' allows for
   flexible object creation.
"""


class Tier:
    def __init__(self, price: float, size: float, quote_id: str = None):
        self.price = price
        self.size = size
        self.quote_id = quote_id

    def __str__(self):
        # Professional format: Price @ Size (ID)
        return f"{self.price} @ {self.size} (ID: {self.quote_id})"


# --- Representing the Order Book ---
# Bids (Buyers)
bids = [
    Tier(100.0, 2, 'b0001'),
    Tier(99.0, 50, 'b0002'),
    Tier(98.0, 12, 'b0003')
]

# Asks (Sellers)
asks = [
    Tier(101.0, 5, 'a0001'),
    Tier(102.0, 7, 'a0002')
]

# 1. Access the Top-of-Book (Index 0)
# We assume the lists are already sorted by price
best_bid = bids[0]
best_ask = asks[0]

# 2. Compute Mid Price
# TODO

# 3. Output results
# TODO
