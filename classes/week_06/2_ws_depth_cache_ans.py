"""
TOPIC: Maintaining a Local Binance Futures Order Book Using FuturesDepthCacheManager

REFERENCE:
https://python-binance.readthedocs.io/en/latest/depth_cache.html

KEY TEACHING POINTS:
1. Depth Stream vs Local Order Book:
   Binance depth websocket streams send incremental updates, not a full order
   book snapshot.

2. Snapshot + Delta Workflow:
   A correct local order book requires:
       - REST snapshot
       - buffered websocket deltas
       - update ID alignment
       - continuous delta application

3. Why Use a Library:
   Maintaining this correctly is easy to get wrong, so this example uses
   python-binance's FuturesDepthCacheManager.

4. FuturesDepthCacheManager:
   The manager maintains a local futures depth cache by combining snapshot and
   websocket updates.

5. Async Context Manager:
   'async with FuturesDepthCacheManager(...)' opens and manages the depth cache
   websocket lifecycle.

6. Receiving Book Updates:
   'await dcm_socket.recv()' waits asynchronously for the next updated depth
   cache.

7. Best Bid and Best Ask:
   'get_bids()[0]' gives the current best bid.
   'get_asks()[0]' gives the current best ask.

8. asyncio.run():
   'asyncio.run(main())' creates the event loop, runs the async program, and
   closes the event loop cleanly.
"""

import asyncio
import logging
from binance import AsyncClient
from binance.ws.depthcache import FuturesDepthCacheManager


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


async def listen_depth_forever(symbol: str) -> None:
    # Switch between production and testnet
    testnet = False
    client = await AsyncClient.create(testnet=testnet)

    try:
        depth_cache_manager = FuturesDepthCacheManager(client, symbol=symbol)

        async with depth_cache_manager as dcm_socket:
            while True:
                depth = await dcm_socket.recv()

                best_bid = depth.get_bids()[0]
                best_ask = depth.get_asks()[0]

                logging.info(
                    "Book | bestBid=%s | bestAsk=%s",
                    best_bid,
                    best_ask,
                )

    finally:
        await client.close_connection()


async def main() -> None:
    await listen_depth_forever("BTCUSDT")


if __name__ == "__main__":
    asyncio.run(main())