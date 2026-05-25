"""
TOPIC: Building an Event-Driven Binance Futures Trading Gateway and Strategy

KEY TEACHING POINTS:
1. Gateway Abstraction:
   BinanceFutureGateway hides exchange connectivity details from the strategy.

2. Callback-Based Design:
   Strategies register callback methods:
       - on_orderbook(book)
       - on_execution(event)
       - on_agg_trade(trade)

3. Event-Driven Architecture:
   The gateway receives exchange events and immediately notifies the strategy.

4. Async Services in Background Thread:
   Market data and execution streams run asynchronously in a dedicated event loop
   thread.

5. Local Order Book:
   FuturesDepthCacheManager maintains the local order book using Binance snapshot
   and depth update logic.

6. Execution Stream:
   User data stream receives private order and fill updates.

7. Post-Only Limit Order:
   timeInForce='GTX' is used for post-only limit orders on Binance Futures.

8. Testnet vs Production:
   testnet=True routes REST and websocket connectivity to Binance Futures testnet.
"""

import asyncio
import logging
import time
from threading import Thread
from typing import Callable
from binance import AsyncClient, Client, BinanceSocketManager
from binance.ws.depthcache import FuturesDepthCacheManager
from common.interface_book import VenueOrderBook, PriceLevel, OrderBook
from common.interface_order import OrderEvent, OrderStatus, ExecutionType, Side
from common.interface_trade import AggTrade

logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


class BinanceFutureGateway:

    def __init__(
        self,
        symbol: str,
        api_key: str,
        api_secret: str,
        name: str = "Binance",
        testnet: bool = True,
    ):
        self._symbol = symbol.upper()
        self._api_key = api_key
        self._api_secret = api_secret
        self._exchange_name = name
        self._testnet = testnet

        self._client: Client | None = None
        self._async_client: AsyncClient | None = None

        self._depth_cache = None

        self._loop = asyncio.new_event_loop()
        self._loop_thread = Thread(
            target=self._run_event_loop,
            daemon=True,
            name=f"{name}-EventLoop",
        )

        self._orderbook_callbacks: list[Callable[[VenueOrderBook], None]] = []
        self._execution_callbacks: list[Callable[[OrderEvent], None]] = []
        self._agg_trade_callbacks: list[Callable[[dict], None]] = []

    def connect(self) -> None:
        logging.info("Starting Binance gateway")

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

        self._loop.create_task(self._listen_orderbook_forever())
        self._loop.create_task(self._listen_execution_forever())
        self._loop.create_task(self._listen_agg_trade_forever())

    async def _listen_orderbook_forever(self) -> None:
        logging.info("Subscribing to Binance Futures depth cache")

        while True:
            try:
                depth_cache_manager = FuturesDepthCacheManager(
                    self._async_client,
                    symbol=self._symbol,
                )

                async with depth_cache_manager as depth_socket:
                    while True:
                        self._depth_cache = await depth_socket.recv()

                        order_book = self.get_order_book()

                        venue_order_book = VenueOrderBook(
                            self._exchange_name,
                            order_book,
                        )

                        for callback in self._orderbook_callbacks:
                            callback(venue_order_book)

            except Exception:
                logging.exception("Depth stream error, reconnecting...")
                await asyncio.sleep(3)

    async def _listen_agg_trade_forever(self) -> None:
        """Subscribes to the aggregate trade stream."""
        logging.info("Subscribing to Binance Futures aggTrade stream")
        while True:
            try:
                bm = BinanceSocketManager(self._async_client)
                # Use aggtrade_futures_socket for futures
                async with bm.aggtrade_futures_socket(self._symbol) as stream:
                    while True:
                        msg = await stream.recv()
                        data = msg.get("data") if "data" in msg else msg
                        if isinstance(data, dict) and data.get("e") == "aggTrade":
                            agg_trade = AggTrade(
                                price=float(data["p"]),
                                size=float(data["q"]),
                                is_buyer_maker=data["m"]
                            )
                            for callback in self._agg_trade_callbacks:
                                callback(agg_trade)
            except Exception:
                logging.exception("aggTrade stream error, reconnecting...")
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
            OrderStatus[order_status],
        )

        order_event.side = Side[side]

        if execution_type == "TRADE":
            order_event.last_filled_price = float(trade_data["L"])
            order_event.last_filled_quantity = float(trade_data["l"])

        for callback in self._execution_callbacks:
            callback(order_event)

    def get_order_book(self) -> OrderBook:
        bids = [
            PriceLevel(price=float(price), size=float(size))
            for price, size in self._depth_cache.get_bids()[:5]
        ]

        asks = [
            PriceLevel(price=float(price), size=float(size))
            for price, size in self._depth_cache.get_asks()[:5]
        ]

        return OrderBook(
            timestamp=self._depth_cache.update_time,
            contract_name=self._symbol,
            bids=bids,
            asks=asks,
        )

    def place_post_only_limit_order(self, side: Side, price: float, quantity: float) -> bool:
        try:
            self._client.futures_create_order(
                symbol=self._symbol,
                side=side.name,
                type="LIMIT",
                price=price,
                quantity=quantity,
                timeInForce="GTX",
            )

            return True

        except Exception as exception:
            logging.exception("Failed to place post-only limit order: %s", exception)
            return False

    def register_orderbook_callback(self, callback: Callable[[VenueOrderBook], None]) -> None:
        self._orderbook_callbacks.append(callback)

    def register_execution_callback(self, callback: Callable[[OrderEvent], None]) -> None:
        self._execution_callbacks.append(callback)

    def register_agg_trade_callback(self, callback: Callable[[dict], None]) -> None:
        self._agg_trade_callbacks.append(callback)


class SimpleStrategy:

    def __init__(self, gateway: BinanceFutureGateway, name: str = "SimpleStrategy"):
        self.name = name
        self.gateway = gateway
        self.start_time = time.time()

        # order and position
        self.order_delay_seconds = 2
        self.order_sent = False
        self.position = 0.0

        # Track net aggressive volume
        self.net_volume = 0.0

        # Track the latest state of the order book
        self.last_book: OrderBook | None = None

    def on_orderbook(self, order_book: VenueOrderBook) -> None:
        book = order_book.get_book()

        # Update local reference
        self.last_book = book

        # print TOB
        best_bid = book.bids[0]
        best_ask = book.asks[0]
        logging.info(
            "[%s] TOB | %.4f @ %.2f | %.2f @ %.4f",
            self.name,
            best_bid.size,
            best_bid.price,
            best_ask.price,
            best_ask.size,
        )

        # Example trading logic:
        # send one post-only order once
        elapsed = time.time() - self.start_time
        if not self.order_sent and elapsed >= self.order_delay_seconds:
            logging.info("[%s] Sending post-only limit order", self.name)

            success = self.gateway.place_post_only_limit_order(
                side=Side.BUY,
                price=25000,
                quantity=0.1,
            )
            if success:
                logging.info("[%s] Sent post-only limit order", self.name)
            else:
                logging.warning("[%s] Failed to post-only limit order", self.name)

            self.order_sent = True

    def on_agg_trade(self, trade: AggTrade) -> None:
        # Update net volume: + for taker buys, - for taker sells
        if trade.is_buy():
            self.net_volume += trade.size
        else:
            self.net_volume -= trade.size

        logging.info(
            "[%s] AGG_TRADE | Net Vol: %.3f | Last: %.3f @ %.2f",
            self.name,
            self.net_volume,
            trade.size,
            trade.price
        )

    def on_execution(self, order_event: OrderEvent) -> None:
        logging.info("[%s] Receive execution: %s",self.name, order_event)

        # Only process fills
        if order_event.execution_type != ExecutionType.TRADE:
            return

        fill_quantity = order_event.last_filled_quantity

        if order_event.side == Side.BUY:
            self.position += fill_quantity
        elif order_event.side == Side.SELL:
            self.position -= fill_quantity

        logging.info("[%s] Position = %.4f",self.name, self.position)


if __name__ == "__main__":
    API_KEY = 'CrIHchQJ5E1a5PqDkrewxyThvcNbGC1sCdDeEjwGjhvHXqWHQFJLfuoHsXkmZPvz'
    API_SECRET = 'cWWLYlLzyjUg4Rv9xxdhiXnozdCKRTCddIghS4m1DIqayJMialFpqDxgp62HPoeC'
    USE_TESTNET = True

    # create a market data and order gateway
    gateway = BinanceFutureGateway(
        symbol="BTCUSDT",
        api_key=API_KEY,
        api_secret=API_SECRET,
        testnet=USE_TESTNET,
    )

    # create strategy
    strategy = SimpleStrategy(gateway)

    # register event handlers
    gateway.register_orderbook_callback(strategy.on_orderbook)
    gateway.register_execution_callback(strategy.on_execution)
    gateway.register_agg_trade_callback(strategy.on_agg_trade)

    # start connection
    gateway.connect()

    while True:
        time.sleep(1)

