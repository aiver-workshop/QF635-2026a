"""
TOPIC: Running an asyncio Event Loop in a Background Thread

KEY TEACHING POINTS:
1. What is an Event Loop:
   An event loop is the core engine of asyncio responsible for:
       - scheduling coroutines
       - pausing coroutines at await points
       - resuming coroutines when ready
       - switching execution between tasks cooperatively

2. One Event Loop per Thread:
   asyncio event loops are generally associated with a single thread.
   Each thread that wants to execute asyncio coroutines requires its own
   event loop.

3. asyncio.run():
   In simple asyncio programs, 'asyncio.run()' automatically:
       - creates an event loop
       - starts the event loop
       - runs the coroutine
       - closes the event loop

   Example:
       asyncio.run(main())

4. Manual Event Loop Creation:
   In background threads, Python does NOT automatically create an event loop.
   Therefore, the loop must be manually created using:

       loop = asyncio.new_event_loop()

5. Associating Loop with Thread:
   'asyncio.set_event_loop(loop)' associates the newly created event loop with
   the current thread.

6. Scheduling Async Tasks:
   'loop.create_task()' schedules a coroutine to execute on the event loop.

7. Long-Running Event Loop:
   'loop.run_forever()' continuously runs the event loop until explicitly
   stopped.

8. Concurrent Behaviour:
   The background asyncio task runs independently while the main thread
   continues executing synchronous code.

9. Cooperative Concurrency:
   Coroutines voluntarily yield execution at 'await' points, allowing the event
   loop to switch between tasks efficiently.

10. Common Real-World Use Cases:
   This architecture is commonly used for:
       - websocket market data listeners
       - trading gateways
       - background network services
       - periodic health checks
       - async message consumers

11. Important Limitation:
   asyncio provides single-threaded cooperative concurrency and is optimized
   primarily for I/O-bound workloads rather than CPU-heavy parallel computation.
"""

import logging
import random
import asyncio
import time
import string
from threading import Thread


logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s] %(message)s",
    level=logging.INFO,
)


def start() -> None:
    """
    Start a background thread that owns and runs an asyncio event loop.
    """
    loop_thread = Thread(
        target=run_event_loop,
        daemon=True,
        name="Async Thread",
    )

    loop_thread.start()


def run_event_loop() -> None:
    """
    Create and run an asyncio event loop inside the background thread.
    """
    # Create a new event loop for this background thread
    loop = asyncio.new_event_loop()

    # Set this loop as the current event loop for this thread
    asyncio.set_event_loop(loop)

    # Schedule multiple async tasks
    loop.create_task(print_random_number_forever())
    loop.create_task(print_random_character_forever())

    # Run the event loop until loop.stop() is called
    loop.run_forever()


async def print_random_number_forever() -> None:
    """
    Print a random integer every second.
    """

    while True:
        logging.info(
            "Random number = %s",
            random.randint(0, 100),
        )

        await asyncio.sleep(1)


async def print_random_character_forever() -> None:
    """
    Print a random character every two seconds.
    """

    while True:
        # TODO print a random character

        await asyncio.sleep(2)


if __name__ == "__main__":
    # Start the background asyncio task
    start()

    # Main thread continues doing normal synchronous work
    while True:
        time.sleep(5)
        logging.info("sanity check from main thread")