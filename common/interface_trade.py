class AggTrade:
    def __init__(self, contract_name: str, price: float, size: float, is_buyer_maker: bool):
        self.contract_name = contract_name
        self.price = price
        self.size = size
        self.is_buyer_maker = is_buyer_maker

    def is_buy(self) -> bool:
        """Returns True if the taker was a buyer (Market Buy)."""
        return not self.is_buyer_maker

    def is_sell(self) -> bool:
        """Returns True if the taker was a seller (Market Sell)."""
        return self.is_buyer_maker
