"""
EXERCISE: Calculate the Mid-Price
Goal: Implement a function that finds the average of a Bid and an Offer.
"""


def calculate_mid(bid_price: float, offer_price: float) -> float:
    """
    TODO
    Calculates the mid-price of a security.

    The mid-price is the average of the highest price a buyer is
    willing to pay (bid) and the lowest price a seller is
    willing to accept (offer).
    """
    pass


# Test the function with a Bid of 100.50 and an Offer of 101.80
mid = calculate_mid(100.50, 101.80)

# Expected Output: 101.15
print(f"The mid-price is: {mid}")