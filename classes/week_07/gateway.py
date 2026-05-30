"""
Reusable Binance Futures gateway for Week 7 market making examples.

The gateway owns exchange connectivity and publishes normalized events to
registered strategy callbacks:
    - on_orderbook(VenueOrderBook)
    - on_agg_trade(AggTrade)
    - on_execution(OrderEvent)
"""

import asyncio
import logging
from threading import Thread
from typing import Callable

from binance import AsyncClient, BinanceSocketManager, Client
from binance.ws.depthcache import FuturesDepthCacheManager

from common.interface_book import OrderBook, PriceLevel, VenueOrderBook
from common.interface_order import ExecutionType, OrderEvent, OrderStatus, Side
from common.interface_trade import AggTrade


class BinanceFutureGateway:

    def __init__(
        self,
        symbols: list[str],
        api_key: str,
        api_secret: str,
        name: str = "Binance",
        testnet: bool = True,
        subscribe_execution: bool = True,
    ):
        self._symbols = [symbol.upper() for symbol in symbols]
        self._api_key = api_key
        self._api_secret = api_secret
        self._exchange_name = name
        self._testnet = testnet
        self._subscribe_execution = subscribe_execution

        self._client: Client | None = None
        self._async_client: AsyncClient | None = None

        self._depth_caches = {}

        self._loop = asyncio.new_event_loop()
        self._loop_thread = Thread(
            target=self._run_event_loop,
            daemon=True,
            name="gw-loop",
        )

        self._orderbook_callbacks: list[Callable[[VenueOrderBook], None]] = []
        self._execution_callbacks: list[Callable[[OrderEvent], None]] = []
        self._agg_trade_callbacks: list[Callable[[AggTrade], None]] = []

    def connect(self) -> None:
        logging.info("Starting Binance gateway for %s", ", ".join(self._symbols))

        self._client = Client(
            self._api_key,
            self._api_secret,
            testnet=self._testnet,
        )

        self._loop_thread.start()

    def _run_event_loop(self) -> None:
        asyncio.set_event_loop(self._loop)

        self._loop.create_task(self._initialize_async_client())
        self._loop.run_forever()

    async def _initialize_async_client(self) -> None:
        self._async_client = await AsyncClient.create(
            self._api_key,
            self._api_secret,
            testnet=self._testnet,
        )

        for symbol in self._symbols:
            self._loop.create_task(self._listen_orderbook_forever(symbol))
            self._loop.create_task(self._listen_agg_trade_forever(symbol))

        if self._subscribe_execution:
            self._loop.create_task(self._listen_execution_forever())

    async def _listen_orderbook_forever(self, symbol: str) -> None:
        logging.info("Subscribing to Binance Futures depth cache for %s", symbol)

        while True:
            try:
                depth_cache_manager = FuturesDepthCacheManager(
                    self._async_client,
                    symbol=symbol,
                )

                async with depth_cache_manager as depth_socket:
                    while True:
                        self._depth_caches[symbol] = await depth_socket.recv()

                        order_book = self.get_order_book(symbol)

                        venue_order_book = VenueOrderBook(
                            self._exchange_name,
                            order_book,
                        )

                        for callback in self._orderbook_callbacks:
                            callback(venue_order_book)

            except Exception:
                logging.exception("Depth stream error for %s, reconnecting...", symbol)
                await asyncio.sleep(3)

    async def _listen_agg_trade_forever(self, symbol: str) -> None:
        logging.info("Subscribing to Binance Futures aggTrade stream for %s", symbol)

        while True:
            try:
                socket_manager = BinanceSocketManager(self._async_client)

                async with socket_manager.aggtrade_futures_socket(symbol) as stream:
                    while True:
                        message = await stream.recv()
                        data = message.get("data") if "data" in message else message

                        if isinstance(data, dict) and data.get("e") == "aggTrade":
                            agg_trade = AggTrade(
                                contract_name=data.get("s", symbol),
                                price=float(data["p"]),
                                size=float(data["q"]),
                                is_buyer_maker=data["m"],
                            )

                            for callback in self._agg_trade_callbacks:
                                callback(agg_trade)

            except Exception:
                logging.exception("aggTrade stream error for %s, reconnecting...", symbol)
                await asyncio.sleep(3)

    async def _listen_execution_forever(self) -> None:
        logging.info("Subscribing to Binance Futures user data stream")

        while True:
            try:
                socket_manager = BinanceSocketManager(self._async_client)

                user_socket = socket_manager.futures_user_socket()
                async with user_socket as websocket:
                    logging.info("Subscribed to futures user data stream")

                    while True:
                        message = await websocket.recv()
                        self._handle_execution_message(message)

            except Exception:
                logging.exception("Execution stream error, reconnecting...")
                await asyncio.sleep(3)

    def _handle_execution_message(self, message: dict) -> None:
        data = message

        if data.get("e") != "ORDER_TRADE_UPDATE":
            return

        trade_data = data["o"]

        client_order_id = trade_data["c"]
        symbol = trade_data["s"]
        execution_type = trade_data["x"]
        order_status = trade_data["X"]
        side = trade_data["S"]

        order_event = OrderEvent(
            symbol,
            client_order_id,
            ExecutionType[execution_type],
            self._map_order_status(order_status),
        )

        order_event.side = Side[side]

        if execution_type == "TRADE":
            order_event.last_filled_price = float(trade_data["L"])
            order_event.last_filled_quantity = float(trade_data["l"])

        for callback in self._execution_callbacks:
            callback(order_event)

    def _map_order_status(self, order_status: str) -> OrderStatus:
        if order_status in OrderStatus.__members__:
            return OrderStatus[order_status]

        if order_status in {"EXPIRED", "EXPIRED_IN_MATCH"}:
            return OrderStatus.CANCELED

        logging.warning("Unknown Binance order status %s, mapping to FAILED", order_status)
        return OrderStatus.FAILED

    def get_order_book(self, symbol: str) -> OrderBook:
        symbol = symbol.upper()
        depth_cache = self._depth_caches[symbol]

        bids = [
            PriceLevel(price=float(price), size=float(size))
            for price, size in depth_cache.get_bids()[:5]
        ]

        asks = [
            PriceLevel(price=float(price), size=float(size))
            for price, size in depth_cache.get_asks()[:5]
        ]

        return OrderBook(
            timestamp=depth_cache.update_time,
            contract_name=symbol,
            bids=bids,
            asks=asks,
        )

    def place_limit_order(
        self,
        symbol: str,
        side: Side,
        price: float,
        quantity: float,
        post_only: bool = True,
    ) -> bool:
        try:
            time_in_force = "GTX" if post_only else "GTC"

            self._client.futures_create_order(
                symbol=symbol.upper(),
                side=side.name,
                type="LIMIT",
                price=price,
                quantity=quantity,
                timeInForce=time_in_force,
            )

            return True

        except Exception as exception:
            logging.exception("Failed to place limit order: %s", exception)
            return False

    def place_market_order(self, symbol: str, side: Side, quantity: float) -> bool:
        try:
            self._client.futures_create_order(
                symbol=symbol.upper(),
                side=side.name,
                type="MARKET",
                quantity=quantity,
            )

            return True

        except Exception as exception:
            logging.exception("Failed to place market order: %s", exception)
            return False

    def register_orderbook_callback(self, callback: Callable[[VenueOrderBook], None]) -> None:
        self._orderbook_callbacks.append(callback)

    def register_execution_callback(self, callback: Callable[[OrderEvent], None]) -> None:
        self._execution_callbacks.append(callback)

    def register_agg_trade_callback(self, callback: Callable[[AggTrade], None]) -> None:
        self._agg_trade_callbacks.append(callback)
