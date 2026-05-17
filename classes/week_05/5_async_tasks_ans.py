"""
TOPIC: Running Multiple Coroutines Concurrently with asyncio Tasks

KEY TEACHING POINTS:
1. Coroutine vs Task:
   Calling an async function creates a coroutine object, but it does not start
   running immediately.

2. Creating Tasks:
   'asyncio.create_task()' schedules a coroutine to run concurrently on the
   event loop as soon as possible.

3. Concurrent Execution:
   Once the tasks are created, all three cooking steps can make progress during
   their waiting periods.

4. Awaiting Tasks:
   'await task' waits for that specific task to complete, but the other scheduled
   tasks can continue running in the background.

5. Runtime Reduction:
   Sequential awaiting takes about:
       2 + 5 + 10 = 17 seconds

   Concurrent task execution takes about:
       max(2, 5, 10) = 10 seconds

6. Cooperative Concurrency:
   Concurrency happens because each coroutine uses 'await asyncio.sleep()',
   which yields control back to the event loop.

7. Important Limitation:
   asyncio is best for I/O-bound waiting tasks such as API calls, websockets,
   database queries, and network requests. It does not make CPU-heavy work
   faster by itself.
"""

import logging
import asyncio
import time


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


async def cut_ingredients() -> None:
    logging.info("Cutting ingredients...")
    await asyncio.sleep(2)
    logging.info("Finished cutting ingredients")


async def cook_food() -> None:
    logging.info("Cooking food...")
    await asyncio.sleep(5)
    logging.info("Finished cooking food")


async def prepare_dessert() -> None:
    logging.info("Preparing dessert...")
    await asyncio.sleep(10)
    logging.info("Finished preparing dessert")


async def cook() -> None:
    logging.info("Start cooking...")

    start = time.perf_counter()

    # Create and schedule tasks.
    # The tasks are allowed to start running as soon as the event loop gets control.
    task_1 = asyncio.create_task(cut_ingredients(), name="Cut Ingredients")
    task_2 = asyncio.create_task(cook_food(), name="Cook Food")
    task_3 = asyncio.create_task(prepare_dessert(), name="Prepare Dessert")

    # Await each task to make sure all tasks complete before cook() returns.
    # Even though we await them one by one, they have already been scheduled,
    # so they can continue progressing concurrently.
    await task_1
    await task_2
    await task_3

    elapsed = time.perf_counter() - start

    logging.info("Finished cooking")
    logging.info("Total runtime = %.2f seconds", elapsed)


if __name__ == "__main__":
    asyncio.run(cook())