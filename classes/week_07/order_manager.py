"""
Order manager abstractions for Week 7.

TradingEngine uses an OrderManager to submit orders. In live trading,
LiveOrderManager forwards orders to BinanceFutureGateway. Later, a simulated
order manager can implement the same methods for backtesting.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from common.interface_order import Side

if TYPE_CHECKING:
    from gateway import BinanceFutureGateway


class OrderManager:

    def place_limit_order(
        self,
        symbol: str,
        side: Side,
        price: float,
        quantity: float,
        post_only: bool = True,
    ) -> bool:
        raise NotImplementedError

    def place_market_order(self, symbol: str, side: Side, quantity: float) -> bool:
        raise NotImplementedError


class LiveOrderManager(OrderManager):

    def __init__(self, gateway: BinanceFutureGateway) -> None:
        self.gateway: BinanceFutureGateway = gateway

    def place_limit_order(
        self,
        symbol: str,
        side: Side,
        price: float,
        quantity: float,
        post_only: bool = True,
    ) -> bool:
        return self.gateway.place_limit_order(
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            post_only=post_only,
        )

    def place_market_order(self, symbol: str, side: Side, quantity: float) -> bool:
        return self.gateway.place_market_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
        )
