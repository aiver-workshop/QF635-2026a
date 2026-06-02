"""
Order manager abstractions for Week 7.

TradingEngine uses an OrderManager to submit orders. In this standalone
backtest folder, SimulatorOrderManager implements the same interface and routes
orders to SimulatedGateway.
"""

from __future__ import annotations

import logging
from typing import Protocol

from common.interface_book import OrderBook
from common.interface_order import Side


class Gateway(Protocol):

    def get_order_book(self, symbol: str) -> OrderBook:
        ...

    def place_limit_order(
        self,
        symbol: str,
        side: Side,
        price: float,
        quantity: float,
        post_only: bool = True,
    ) -> bool:
        ...

    def place_market_order(self, symbol: str, side: Side, quantity: float) -> bool:
        ...


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

    def __init__(
        self,
        gateway: Gateway,
        max_order_notional: float | None = None,
    ) -> None:
        self.gateway: Gateway = gateway
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
            logging.error(
                "[LiveOrderManager] market order rejected | %s %s %.6f reason=no_order_book",
                symbol,
                side.name,
                quantity,
            )
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

        if self.max_order_notional is None:
            self.last_rejection = None
            logging.info(
                "[LiveOrderManager] %s order check passed | %s %s %.6f @ %.2f notional=%.2f max_order_notional=None",
                order_type,
                symbol,
                side.name,
                quantity,
                price,
                order_notional,
            )
            return True

        if order_notional <= self.max_order_notional:
            self.last_rejection = None
            logging.info(
                "[LiveOrderManager] %s order check passed | %s %s %.6f @ %.2f notional=%.2f max_order_notional=%.2f",
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
            "[LiveOrderManager] %s order rejected | %s %s %.6f @ %.2f notional=%.2f max_order_notional=%.2f",
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
        except Exception:
            logging.exception(
                "[LiveOrderManager] failed to get order book for market order check | %s",
                symbol,
            )
            return None

        if side == Side.BUY:
            return book.get_best_ask()

        return book.get_best_bid()
