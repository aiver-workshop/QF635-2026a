"""
TOPIC: Running Multiple Coroutines Concurrently with asyncio.gather

KEY TEACHING POINTS:
1. asyncio.gather():
   'asyncio.gather()' schedules multiple coroutines concurrently and waits for
   all of them to complete.

2. Concurrent Coroutine Execution:
   All cooking tasks begin execution together and make progress during their
   waiting periods.

3. Automatic Task Management:
   Unlike 'asyncio.create_task()', 'asyncio.gather()' automatically wraps
   coroutines into tasks internally.

4. Cooperative Scheduling:
   Coroutines voluntarily yield control back to the event loop whenever they
   encounter an 'await' statement.

5. Runtime Improvement:
   Sequential execution would take approximately:
       2 + 5 + 10 = 17 seconds

   Concurrent execution with gather takes approximately:
       max(2, 5, 10) = 10 seconds

6. Result Collection:
   'asyncio.gather()' returns results from all coroutines in the same order
   they were passed into gather().

7. Common asyncio Pattern:
   asyncio.gather() is one of the most common ways to run multiple I/O-bound
   operations concurrently, such as:
       - API calls
       - websocket requests
       - database queries
       - market data subscriptions
"""

import asyncio
import logging
import time


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


async def cut_ingredients() -> str:
    logging.info("Cutting ingredients...")

    await asyncio.sleep(2)

    logging.info("Finished cutting ingredients")

    return "Ingredients ready"


async def cook_food() -> str:
    logging.info("Cooking food...")

    await asyncio.sleep(5)

    logging.info("Finished cooking food")

    return "Main course ready"


async def prepare_dessert() -> str:
    logging.info("Preparing dessert...")

    await asyncio.sleep(10)

    logging.info("Finished preparing dessert")

    return "Dessert ready"


async def cook() -> None:
    logging.info("Start cooking workflow")

    start = time.perf_counter()

    # TODO Run all cooking methods concurrently using gather() to automatically schedules them as tasks.
    results = await asyncio.gather(
        cut_ingredients()
    )

    elapsed = time.perf_counter() - start

    logging.info("All cooking tasks completed")

    logging.info("Results returned from gather:")
    for result in results:
        logging.info(result)

    logging.info("Total runtime = %.2f seconds", elapsed)


if __name__ == "__main__":
    asyncio.run(cook())