"""
TOPIC: Listening to Binance Futures User Data Stream Using python-binance for execution report

REFERENCE:
https://python-binance.readthedocs.io/en/latest/websockets.html

KEY TEACHING POINTS:
1. User Data Stream:
   User data streams provide private account updates such as:
       - order updates
       - fills
       - account balance changes
       - position updates

2. python-binance WebSocket Manager:
   BinanceSocketManager simplifies websocket management by internally handling:
       - websocket connection
       - listenKey creation
       - message routing

3. Async WebSocket Processing:
   User updates are processed asynchronously using the asyncio event loop.

4. ORDER_TRADE_UPDATE:
   This event contains order lifecycle updates including:
       - NEW
       - PARTIALLY_FILLED
       - FILLED
       - CANCELED

5. Separation of Concerns:
   Websocket subscription logic and message handling are separated into
   different methods.

6. Testnet Support:
   testnet=True routes both REST and websocket connections to Binance Futures
   testnet infrastructure.

7. Real Trading Systems:
   User data streams are essential for:
       - execution systems
       - position tracking
       - portfolio management
       - risk systems
       - order management systems
"""

import asyncio
import logging
from binance import AsyncClient, BinanceSocketManager


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


class BinanceUserDataClient:

    def __init__(self, api_key: str, api_secret: str, use_testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.use_testnet = use_testnet
        self.client = None

    async def subscribe(self) -> None:
        logging.info(
            "Connecting to Binance Futures (%s)",
            "TESTNET" if self.use_testnet else "PRODUCTION",
        )

        self.client = await AsyncClient.create(
            api_key=self.api_key,
            api_secret=self.api_secret,
            testnet=self.use_testnet,
        )

        # BinanceSocketManager internally manages:
        # - websocket connection
        # - listenKey creation
        # - websocket lifecycle
        socket_manager = BinanceSocketManager(self.client)

        # Create futures user data websocket stream
        user_socket = socket_manager.futures_user_socket()

        async with user_socket as websocket:
            logging.info("Subscribed to futures user data stream")

            while True:
                # handle user data message
                message = await websocket.recv()
                self.handle_message(message)

    def handle_message(self, message: dict) -> None:
        # identify execution report from user data message
        pass

    def handle_order_trade_update(self, message: dict) -> None:
        # TODO handle execution report
        pass

    async def close(self) -> None:
        # TODO close connection
        pass


async def main() -> None:
    API_KEY = 'CrIHchQJ5E1a5PqDkrewxyThvcNbGC1sCdDeEjwGjhvHXqWHQFJLfuoHsXkmZPvz'
    API_SECRET = 'cWWLYlLzyjUg4Rv9xxdhiXnozdCKRTCddIghS4m1DIqayJMialFpqDxgp62HPoeC'
    USE_TESTNET = True

    client = BinanceUserDataClient(api_key=API_KEY, api_secret=API_SECRET, use_testnet=USE_TESTNET)
    try:
        await client.subscribe()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())