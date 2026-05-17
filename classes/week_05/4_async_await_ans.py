"""
TOPIC: Sequential Coroutine Execution with asyncio

KEY TEACHING POINTS:
1. Coroutines:
   Functions declared with 'async def' are called coroutines and can be paused
   and resumed during execution.

2. Awaiting Coroutines:
   Using 'await' on a coroutine pauses the current coroutine until the awaited
   coroutine completes execution.

3. Sequential Async Execution:
   Even though the methods are asynchronous, awaiting coroutines one-by-one
   still executes them sequentially.

4. Blocking at Coroutine Level:
   While 'await' does not block the entire thread, it does block the current
   coroutine until the awaited operation finishes.

5. Cooperative Scheduling:
   During 'await asyncio.sleep()', the coroutine voluntarily yields control back
   to the asyncio event loop.

6. Event Loop:
   'asyncio.run()' creates and manages the event loop responsible for scheduling
   coroutine execution.

7. Important Distinction:
   Asyncio does NOT automatically make code parallel or concurrent.
   Sequential 'await' behaves similarly to normal synchronous function calls.

8. Total Runtime:
   Since tasks execute sequentially:
       2 + 5 + 10 = approximately 17 seconds total runtime.

9. Foundation for Concurrent Coroutines:
   In the next exercise, coroutines will be converted into Tasks so they can
   execute concurrently using the same event loop.
"""

import asyncio
import logging
import time


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


async def cut_ingredients():
    logging.info("Cutting ingredients...")

    await asyncio.sleep(2)

    logging.info("Finished cutting ingredients")


async def cook_food():
    logging.info("Cooking food...")

    await asyncio.sleep(5)

    logging.info("Finished cooking food")


async def prepare_dessert():
    logging.info("Preparing dessert...")

    await asyncio.sleep(10)

    logging.info("Finished preparing dessert")


async def cook():
    """
    Execute coroutines sequentially.

    Each coroutine must complete before the next coroutine starts.
    """

    await cut_ingredients()

    await cook_food()

    await prepare_dessert()


if __name__ == "__main__":

    logging.info("Starting cooking workflow")

    start = time.perf_counter()

    # Run the async function using the asyncio event loop
    asyncio.run(cook())

    elapsed = time.perf_counter() - start

    logging.info("Cooking workflow completed")
    logging.info("Total runtime = %.2f seconds", elapsed)