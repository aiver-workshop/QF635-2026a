"""
TOPIC: Building an Event-Driven BTC/ETH Pair Trading Strategy on Binance Futures

KEY TEACHING POINTS:
1. Multi-Symbol Gateway:
   A single gateway can manage more than one contract.

2. Per-Symbol Market Data:
   Each symbol gets its own depth cache stream and aggTrade stream.

3. Shared Execution Stream:
   The futures user data stream is account-level, so one execution stream can
   receive order updates for all symbols.

4. Contract-Aware Events:
   OrderBook, OrderEvent, and AggTrade events carry their contract name so the
   strategy can keep separate state per symbol.

5. Pair Trading Strategy:
   The strategy compares BTCUSDT and ETHUSDT using a rolling log-price spread
   and generates entry/exit signals from the spread z-score.

6. Actual Fill PnL:
   Realized PnL is updated from execution events using the actual filled price
   and filled quantity reported by Binance.
"""

import asyncio
import logging
import math
import time
from collections import deque
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
            name=f"{name}-EventLoop",
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
                bm = BinanceSocketManager(self._async_client)

                async with bm.aggtrade_futures_socket(symbol) as stream:
                    while True:
                        msg = await stream.recv()
                        data = msg.get("data") if "data" in msg else msg

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


class PairTradingStrategy:

    def __init__(
        self,
        gateway: BinanceFutureGateway,
        base_symbol: str,
        hedge_symbol: str,
        name: str = "PairTradingStrategy",
    ):
        self.name = name
        self.gateway = gateway
        self.base_symbol = base_symbol.upper()
        self.hedge_symbol = hedge_symbol.upper()
        self.symbols = [self.base_symbol, self.hedge_symbol]

        self.position = {symbol: 0.0 for symbol in self.symbols}
        self.net_volume = {symbol: 0.0 for symbol in self.symbols}
        self.last_book: dict[str, OrderBook] = {}

        self.hedge_ratio = 1.0
        self.spread_window = deque(maxlen=120)
        self.entry_z_score = 2.0
        self.exit_z_score = 0.5

        # -1 = short spread, 0 = flat, 1 = long spread
        self.pair_state = 0

        # Keep trading disabled until the user intentionally turns it on.
        self.enable_trading = False
        self.base_order_quantity = 0.001
        self.hedge_order_quantity = 0.01
        self.average_entry_price = {symbol: 0.0 for symbol in self.symbols}
        self.realized_pnl = 0.0
        self.current_pair_pnl = 0.0
        self.exit_in_progress = False

        self.last_log_time = 0.0
        self.log_interval_seconds = 1
        self.last_window_log_time = 0.0

    def on_orderbook(self, order_book: VenueOrderBook) -> None:
        book = order_book.get_book()
        symbol = book.contract_name

        self.last_book[symbol] = book
        self.evaluate_pair()

    def evaluate_pair(self) -> None:
        if self.exit_in_progress:
            return

        if self.base_symbol not in self.last_book:
            return

        if self.hedge_symbol not in self.last_book:
            return

        base_mid = self.get_mid_price(self.last_book[self.base_symbol])
        hedge_mid = self.get_mid_price(self.last_book[self.hedge_symbol])

        spread = math.log(base_mid) - self.hedge_ratio * math.log(hedge_mid)
        self.spread_window.append(spread)

        if len(self.spread_window) < self.spread_window.maxlen:
            self.log_window_warmup()
            return

        mean = sum(self.spread_window) / len(self.spread_window)
        variance = sum((value - mean) ** 2 for value in self.spread_window) / len(self.spread_window)
        standard_deviation = math.sqrt(variance)

        if standard_deviation == 0:
            return

        z_score = (spread - mean) / standard_deviation
        self.log_pair_state(base_mid, hedge_mid, spread, z_score)

        if self.pair_state == 0:
            if z_score >= self.entry_z_score:
                self.enter_short_spread(z_score)
            elif z_score <= -self.entry_z_score:
                self.enter_long_spread(z_score)

        elif self.pair_state == 1 and z_score >= -self.exit_z_score:
            self.exit_pair(z_score)

        elif self.pair_state == -1 and z_score <= self.exit_z_score:
            self.exit_pair(z_score)

    def get_mid_price(self, book: OrderBook) -> float:
        return (book.get_best_bid() + book.get_best_ask()) / 2

    def log_window_warmup(self) -> None:
        now = time.time()
        if now - self.last_window_log_time < self.log_interval_seconds:
            return

        self.last_window_log_time = now
        logging.info(
            "[%s] Waiting for spread window %s/%s",
            self.name,
            len(self.spread_window),
            self.spread_window.maxlen,
        )

    def log_pair_state(
        self,
        base_mid: float,
        hedge_mid: float,
        spread: float,
        z_score: float,
    ) -> None:
        now = time.time()
        if now - self.last_log_time < self.log_interval_seconds:
            return

        self.last_log_time = now
        logging.info(
            "[%s] PAIR %s/%s | base_mid=%.2f hedge_mid=%.2f spread=%.6f z=%.2f state=%s",
            self.name,
            self.base_symbol,
            self.hedge_symbol,
            base_mid,
            hedge_mid,
            spread,
            z_score,
            self.pair_state,
        )

    def enter_long_spread(self, z_score: float) -> None:
        logging.info(
            "[%s] SIGNAL long spread z=%.2f | BUY %s, SELL %s",
            self.name,
            z_score,
            self.base_symbol,
            self.hedge_symbol,
        )

        if self.enable_trading:
            orders = self.send_pair_orders(base_side=Side.BUY, hedge_side=Side.SELL)
            if self.orders_sent(orders):
                self.current_pair_pnl = 0.0
                self.exit_in_progress = False
                self.pair_state = 1
                logging.info("[%s] Entry orders submitted; waiting for execution fills", self.name)
            else:
                logging.warning("[%s] Entry incomplete; pair state remains flat", self.name)
        else:
            self.pair_state = 1
            self.log_trading_disabled()

    def enter_short_spread(self, z_score: float) -> None:
        logging.info(
            "[%s] SIGNAL short spread z=%.2f | SELL %s, BUY %s",
            self.name,
            z_score,
            self.base_symbol,
            self.hedge_symbol,
        )

        if self.enable_trading:
            orders = self.send_pair_orders(base_side=Side.SELL, hedge_side=Side.BUY)
            if self.orders_sent(orders):
                self.current_pair_pnl = 0.0
                self.exit_in_progress = False
                self.pair_state = -1
                logging.info("[%s] Entry orders submitted; waiting for execution fills", self.name)
            else:
                logging.warning("[%s] Entry incomplete; pair state remains flat", self.name)
        else:
            self.pair_state = -1
            self.log_trading_disabled()

    def exit_pair(self, z_score: float) -> None:
        logging.info("[%s] SIGNAL exit pair z=%.2f", self.name, z_score)

        if self.enable_trading:
            if self.pair_state == 1:
                orders = self.send_pair_orders(base_side=Side.SELL, hedge_side=Side.BUY)
            elif self.pair_state == -1:
                orders = self.send_pair_orders(base_side=Side.BUY, hedge_side=Side.SELL)
            else:
                return

            if not self.orders_sent(orders):
                logging.warning("[%s] Exit incomplete; pair state remains %s", self.name, self.pair_state)
                return

            self.exit_in_progress = True
            logging.info("[%s] Exit orders submitted; waiting for execution fills to finalize PnL", self.name)
        else:
            self.log_trading_disabled()
            self.pair_state = 0

    def log_trading_disabled(self) -> None:
        logging.info("[%s] Trading disabled; signal logged but no orders sent", self.name)

    def send_pair_orders(self, base_side: Side, hedge_side: Side) -> dict:
        base_sent = self.gateway.place_market_order(
            symbol=self.base_symbol,
            side=base_side,
            quantity=self.base_order_quantity,
        )

        logging.info(
            "[%s] Sent market order %s %s %.6f | success=%s",
            self.name,
            base_side.name,
            self.base_symbol,
            self.base_order_quantity,
            base_sent,
        )

        hedge_sent = self.gateway.place_market_order(
            symbol=self.hedge_symbol,
            side=hedge_side,
            quantity=self.hedge_order_quantity,
        )

        logging.info(
            "[%s] Sent market order %s %s %.6f | success=%s",
            self.name,
            hedge_side.name,
            self.hedge_symbol,
            self.hedge_order_quantity,
            hedge_sent,
        )

        return {
            "base_side": base_side,
            "hedge_side": hedge_side,
            "base_quantity": self.base_order_quantity,
            "hedge_quantity": self.hedge_order_quantity,
            "base_sent": base_sent,
            "hedge_sent": hedge_sent,
        }

    def orders_sent(self, orders: dict) -> bool:
        return orders["base_sent"] and orders["hedge_sent"]

    def on_agg_trade(self, trade: AggTrade) -> None:
        symbol = trade.contract_name

        if symbol not in self.net_volume:
            self.net_volume[symbol] = 0.0

        if trade.is_buy():
            self.net_volume[symbol] += trade.size
        else:
            self.net_volume[symbol] -= trade.size

    def on_execution(self, order_event: OrderEvent) -> None:
        symbol = order_event.contract_name
        logging.info("[%s] Receive execution for %s: %s", self.name, symbol, order_event)

        if order_event.execution_type != ExecutionType.TRADE:
            return

        if symbol not in self.position:
            self.position[symbol] = 0.0
            self.average_entry_price[symbol] = 0.0

        fill_pnl = self.update_position_from_fill(
            symbol=symbol,
            side=order_event.side,
            fill_price=order_event.last_filled_price,
            fill_quantity=order_event.last_filled_quantity,
        )

        logging.info(
            "[%s] Fill %s %s %.6f @ %.2f | fill_pnl=%.4f realized=%.4f",
            self.name,
            order_event.side.name,
            symbol,
            order_event.last_filled_quantity,
            order_event.last_filled_price,
            fill_pnl,
            self.realized_pnl,
        )

        logging.info(
            "[%s] Position %s = %.6f avg_entry=%.2f",
            self.name,
            symbol,
            self.position[symbol],
            self.average_entry_price[symbol],
        )

        self.check_exit_complete()

    def update_position_from_fill(
        self,
        symbol: str,
        side: Side,
        fill_price: float,
        fill_quantity: float,
    ) -> float:
        old_position = self.position[symbol]
        old_average_price = self.average_entry_price[symbol]
        signed_quantity = fill_quantity if side == Side.BUY else -fill_quantity

        if old_position == 0 or old_position * signed_quantity > 0:
            new_position = old_position + signed_quantity
            new_average_price = (
                (abs(old_position) * old_average_price) + (fill_quantity * fill_price)
            ) / abs(new_position)

            self.position[symbol] = new_position
            self.average_entry_price[symbol] = new_average_price
            return 0.0

        closed_quantity = min(abs(old_position), fill_quantity)
        fill_pnl = self.calculate_fill_pnl(
            old_position=old_position,
            average_price=old_average_price,
            fill_price=fill_price,
            closed_quantity=closed_quantity,
        )

        new_position = old_position + signed_quantity

        if abs(new_position) < 0.00000001:
            self.position[symbol] = 0.0
            self.average_entry_price[symbol] = 0.0
        elif old_position * new_position > 0:
            self.position[symbol] = new_position
        else:
            self.position[symbol] = new_position
            self.average_entry_price[symbol] = fill_price

        self.realized_pnl += fill_pnl
        self.current_pair_pnl += fill_pnl

        return fill_pnl

    def calculate_fill_pnl(
        self,
        old_position: float,
        average_price: float,
        fill_price: float,
        closed_quantity: float,
    ) -> float:
        if old_position > 0:
            return (fill_price - average_price) * closed_quantity

        return (average_price - fill_price) * closed_quantity

    def check_exit_complete(self) -> None:
        if not self.exit_in_progress:
            return

        base_flat = abs(self.position.get(self.base_symbol, 0.0)) < 0.00000001
        hedge_flat = abs(self.position.get(self.hedge_symbol, 0.0)) < 0.00000001

        if not base_flat or not hedge_flat:
            return

        logging.info(
            "[%s] EXIT PNL from actual fills | trade=%.4f cumulative=%.4f",
            self.name,
            self.current_pair_pnl,
            self.realized_pnl,
        )
        logging.info("[%s] TOTAL PNL = %.4f", self.name, self.realized_pnl)

        self.current_pair_pnl = 0.0
        self.exit_in_progress = False
        self.pair_state = 0


if __name__ == "__main__":
    API_KEY = "CrIHchQJ5E1a5PqDkrewxyThvcNbGC1sCdDeEjwGjhvHXqWHQFJLfuoHsXkmZPvz"
    API_SECRET = "cWWLYlLzyjUg4Rv9xxdhiXnozdCKRTCddIghS4m1DIqayJMialFpqDxgp62HPoeC"
    USE_TESTNET = True
    ENABLE_TRADING = True

    SYMBOLS = ["BTCUSDT", "ETHUSDT"]

    gateway = BinanceFutureGateway(
        symbols=SYMBOLS,
        api_key=API_KEY,
        api_secret=API_SECRET,
        testnet=USE_TESTNET,
        subscribe_execution=True,
    )

    strategy = PairTradingStrategy(
        gateway=gateway,
        base_symbol="BTCUSDT",
        hedge_symbol="ETHUSDT",
    )
    strategy.enable_trading = ENABLE_TRADING

    gateway.register_orderbook_callback(strategy.on_orderbook)
    gateway.register_execution_callback(strategy.on_execution)
    gateway.register_agg_trade_callback(strategy.on_agg_trade)

    gateway.connect()

    while True:
        time.sleep(1)
