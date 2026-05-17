"""
TOPIC: Write a gateway class to maintaining a local Binance Futures order book

REFERENCE:
https://python-binance.readthedocs.io/en/latest/depth_cache.html

KEY TEACHING POINTS:
1. Depth Stream vs Local Order Book:
   Binance depth websocket streams only publish incremental updates, not full
   order book snapshots.

2. FuturesDepthCacheManager:
   The manager automatically:
       - fetches the initial snapshot
       - buffers websocket updates
       - applies updates in sequence
       - maintains a synchronized local order book

3. Object-Oriented Design:
   The websocket client and order book handling logic are encapsulated inside
   a reusable class.

4. Async Market Data Processing:
   The depth cache manager runs asynchronously using the asyncio event loop.

5. Best Bid and Ask:
   The local depth cache provides direct access to:
       - best bid
       - best ask
       - full local order book state

6. Production vs Testnet:
   'testnet=True' routes both REST and websocket connections to Binance Futures
   testnet infrastructure.

7. Separation of Concerns:
   Connection management and book handling logic are separated into different
   methods.

8. Real Trading Systems:
   Similar architectures are commonly used in:
       - market making systems
       - execution engines
       - smart order routers
       - liquidity analytics
       - HFT infrastructure
"""

import asyncio
import logging
from binance import AsyncClient
from binance.ws.depthcache import FuturesDepthCacheManager


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


class BinanceDepthGateway:

    def __init__(self, symbol: str, use_testnet: bool = True):
        self.symbol = symbol.upper()
        self.use_testnet = use_testnet
        self.client = None

    async def subscribe(self) -> None:
        logging.info(
            "Connecting to Binance Futures (%s)",
            "TESTNET" if self.use_testnet else "PRODUCTION",
        )

        # testnet=True automatically switches both REST and websocket
        # connections to Binance Futures testnet infrastructure.
        self.client = await AsyncClient.create(
            testnet=self.use_testnet,
        )

        # stream update frequency: 100ms, 500ms, 1000ms
        depth_cache_manager = FuturesDepthCacheManager(
            self.client,
            symbol=self.symbol,
            refresh_interval=100,
            limit=100
        )

        async with depth_cache_manager as dcm_socket:
            logging.info("Subscribed to depth cache for %s",self.symbol)

            while True:
                # Wait asynchronously for the next updated local depth cache
                depth_cache = await dcm_socket.recv()
                # handle book update
                self.handle_depth_cache(depth_cache)

    def handle_depth_cache(self, depth_cache) -> None:
        # print depth
        best_bid = depth_cache.get_bids()[0]
        best_ask = depth_cache.get_asks()[0]
        best_bid_price = float(best_bid[0])
        best_bid_quantity = float(best_bid[1])
        best_ask_price = float(best_ask[0])
        best_ask_quantity = float(best_ask[1])
        spread = best_ask_price - best_bid_price
        logging.info(
            "%s | bestBid=%.2f qty=%.4f | "
            "bestAsk=%.2f qty=%.4f | spread=%.2f",
            self.symbol,
            best_bid_price,
            best_bid_quantity,
            best_ask_price,
            best_ask_quantity,
            spread,
        )

    async def close(self) -> None:
        if self.client is not None:
            await self.client.close_connection()


async def main() -> None:
    client = BinanceDepthGateway(symbol="BTCUSDT", use_testnet=False)
    try:
        await client.subscribe()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())