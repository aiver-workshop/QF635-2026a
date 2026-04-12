"""
TOPIC: The '__main__' Entry Point and Script Execution
REFERENCE: https://realpython.com

KEY TEACHING POINTS:
1. Script vs. Module: Python executes code from top to bottom. If a script is
   imported, all global code runs. The 'if __name__ == "__main__"' block
   prevents this "auto-run" behavior.
2. Entry Point: In professional projects, this idiom defines the official
   starting point of your program, making the code easier to debug and trace.
3. Scope Control: Variables defined inside the 'if' block are not
   automatically available to other scripts that import this file,
   promoting "clean" code.
4. Best Practice Placement: This block is traditionally placed at the
   absolute bottom of the file.
"""

import time
import logging

# Configuration is global so it applies to all functions in the file
logging.basicConfig(
    format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s',
    level=logging.INFO
)


def start_counter():
    """Encapsulating logic in a function makes it reusable by other scripts."""
    number = 1
    try:
        while True:
            logging.info(f"Tick: {number}")
            time.sleep(1)
            number += 1
    except KeyboardInterrupt:
        logging.info("Counter stopped by user.")


# This guard ensures the counter only starts if we run THIS file directly
if __name__ == '__main__':
    logging.info("Program started via direct execution.")
    start_counter()
