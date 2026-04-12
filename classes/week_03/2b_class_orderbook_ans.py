"""
TOPIC: Volume-Weighted Average Price (VWAP) Calculation
REFERENCE: https://wikipedia.org

KEY TEACHING POINTS:
1. VWAP Calculation: The formula is (Sum of Price * Size) / (Total Size).
   This provides a more accurate "average" price for large orders.
2. List Comprehensions in Classes: Using 'sum()' with a generator expression
   is the most efficient way to process a list of objects.
3. Weighted Mid: By combining the Bid VWAP and Ask VWAP, you can calculate
   a "Fair Value" that accounts for all visible depth, not just the top level.
4. Error Prevention: Always check if the 'total_size' is greater than zero
   to avoid a 'ZeroDivisionError'.
"""
from datetime import datetime


class Tier:
    def __init__(self, price: float, size: float, quote_id: str = None):
        self.price = price
        self.size = size
        self.quote_id = quote_id

    def __str__(self):
        return f"({self.price}, {self.size})"


class OrderBook:
    def __init__(self, timestamp: datetime, bids: list[Tier], asks: list[Tier]):
        self.timestamp = timestamp
        self.bids = bids
        self.asks = asks

    def best_bid(self) -> float:
        return self.bids[0].price if self.bids else 0.0

    def best_ask(self) -> float:
        return self.asks[0].price if self.asks else 0.0

    def mid(self) -> float:
        """Standard mid from top-of-book."""
        return 0.5 * (self.best_bid() + self.best_ask())

    def calculate_side_vwap(self, side: list[Tier]) -> float:
        """Helper method to calculate VWAP for a specific list of Tiers."""
        if not side:
            return 0.0

        # Formula: Sum(Price * Size) / Total_Size
        total_notional = sum(t.price * t.size for t in side)
        total_size = sum(t.size for t in side)

        return total_notional / total_size if total_size > 0 else 0.0

    def vwap_mid(self) -> float:
        """Calculates a mid-price based on the VWAP of both sides."""
        bid_vwap = self.calculate_side_vwap(self.bids)
        ask_vwap = self.calculate_side_vwap(self.asks)
        return 0.5 * (bid_vwap + ask_vwap)

    def __str__(self):
        return f"OB @ {self.timestamp} | Mid: {self.mid():.2f} | VWAP Mid: {self.vwap_mid():.2f}"


# --- Execution ---
if __name__ == '__main__':
    # Bids: Most liquidity is at the top (100)
    bids = [Tier(100, 10, 'b1'), Tier(99, 2, 'b2'), Tier(98, 1, 'b3')]

    # Asks: Most liquidity is at the bottom (103)
    asks = [Tier(101, 1, 'a1'), Tier(102, 2, 'a2'), Tier(103, 10, 'a3')]

    ob = OrderBook(datetime.now(), bids, asks)

    print(ob)
    print(f"Standard Mid: {ob.mid():.2f}")
    print(f"VWAP Mid:     {ob.vwap_mid():.2f}")
