"""
Simulator order manager for backtesting.

TradingEngine calls this object exactly like it calls LiveOrderManager. The
difference is that orders are routed to SimulatedGateway instead of Binance.
"""

from __future__ import annotations

import logging

from common.interface_order import Side
from order_manager import OrderManager
from simulated_gateway import SimulatedGateway


class SimulatorOrderManager(OrderManager):

    def __init__(
        self,
        gateway: SimulatedGateway,
        max_order_notional: float | None = None,
    ) -> None:
        self.gateway: SimulatedGateway = gateway
        self.max_order_notional: float | None = max_order_notional
        self.last_rejection: dict | None = None

    def place_limit_order(
        self,
        symbol: str,
        side: Side,
        price: float,
        quantity: float,
        post_only: bool = True,
    ) -> bool:
        self.last_rejection = None

        if not self._is_order_notional_allowed(
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            order_type="LIMIT",
        ):
            return False

        return self.gateway.place_limit_order(
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            post_only=post_only,
        )

    def place_market_order(self, symbol: str, side: Side, quantity: float) -> bool:
        self.last_rejection = None
        reference_price = self._get_market_order_reference_price(symbol, side)

        if reference_price is None:
            self.last_rejection = {
                "symbol": symbol,
                "side": side.name,
                "quantity": quantity,
                "price": 0.0,
                "notional": 0.0,
                "max_order_notional": self.max_order_notional,
                "reason": "no_order_book",
            }
            return False

        if not self._is_order_notional_allowed(
            symbol=symbol,
            side=side,
            price=reference_price,
            quantity=quantity,
            order_type="MARKET",
        ):
            return False

        return self.gateway.place_market_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
        )

    def get_last_rejection(self) -> dict | None:
        return self.last_rejection

    def _is_order_notional_allowed(
        self,
        symbol: str,
        side: Side,
        price: float,
        quantity: float,
        order_type: str,
    ) -> bool:
        order_notional = abs(price * quantity)

        if self.max_order_notional is None or order_notional <= self.max_order_notional:
            logging.info(
                "[SimulatorOrderManager] %s order check passed | %s %s %.6f @ %.2f notional=%.2f max_order_notional=%s",
                order_type,
                symbol,
                side.name,
                quantity,
                price,
                order_notional,
                self.max_order_notional,
            )
            return True

        self.last_rejection = {
            "symbol": symbol,
            "side": side.name,
            "quantity": quantity,
            "price": price,
            "notional": order_notional,
            "max_order_notional": self.max_order_notional,
            "reason": f"notional {order_notional:.2f} > limit {self.max_order_notional:.2f}",
        }
        logging.error(
            "[SimulatorOrderManager] %s order rejected | %s %s %.6f @ %.2f notional=%.2f max_order_notional=%.2f",
            order_type,
            symbol,
            side.name,
            quantity,
            price,
            order_notional,
            self.max_order_notional,
        )
        return False

    def _get_market_order_reference_price(self, symbol: str, side: Side) -> float | None:
        try:
            book = self.gateway.get_order_book(symbol)
        except KeyError:
            return None

        if side == Side.BUY:
            return book.get_best_ask()

        return book.get_best_bid()
