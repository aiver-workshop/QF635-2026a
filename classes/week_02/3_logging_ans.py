"""
EXERCISE: Structured Logging
Goal: Replace print() with logging to create a professional execution record.

Reference: https://realpython.com/python-logging/
"""
import logging
import time

# Configure the 'Root Logger'
# asctime: Timestamp | threadName: Which thread | levelname: Severity | message: The data
logging.basicConfig(
    format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s',
    level=logging.INFO
)

number = 1

try:
    while True:
        # Use .info() instead of print()
        logging.info(f"Current Value: {number}")

        # Pause for 2 seconds
        time.sleep(2)

        number += 1
except KeyboardInterrupt:
    logging.warning("Process interrupted by user.")
