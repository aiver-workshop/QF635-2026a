"""
================================================================================
SCRIPT: producer_modular.py
ROLE: Modular Stock Price Data Generator (Data Source with Main Block)
DESIGN:
    - Isolates the price calculations inside a swappable function.
    - Uses a structured main() execution block to control workflow.
    - Persists real-time data directly to a local CSV file with an atomic temp swap.
    - Enforces a strict memory constraint of 1,000 max history rows on disk.
DEPENDENCIES: Python Standard Library (os, random, time, datetime)
================================================================================
"""

import os
import random
import time
from datetime import datetime

# Global Configuration Constants
INTERVAL_SECONDS = 1
FILE_NAME = "realtime_stock_prices.csv"
MAX_LINES = 1000

# Global tracking variable for simulation fallback
_SIMULATED_PRICE_STATE = 150.00


def fetch_next_market_price() -> float:
    """
    Data ingestion abstraction function.

    CURRENT STATUS: Simulated random walk data stream.
    FUTURE UPGRADE: Replace this entire function block with a real connection
                   (e.g., 'return my_broker_api.get_live_ticker("AAPL")').

    Returns:
        float: The most up-to-date market price value.
    """
    global _SIMULATED_PRICE_STATE

    # Simulation configuration variables
    VOLATILITY = 0.002
    DRIFT = 0.0001

    # Calculate random movement
    pct_change = random.uniform(-VOLATILITY, VOLATILITY) + DRIFT
    _SIMULATED_PRICE_STATE = max(0.01, _SIMULATED_PRICE_STATE * (1 + pct_change))

    return round(_SIMULATED_PRICE_STATE, 2)


def main():
    """
    Main orchestration loop for the producer runtime environment.
    Handles data gathering loops, disk file operations, and window capping.
    """
    print(f"Starting Modular Producer Engine (Cap: {MAX_LINES} lines)...")
    print("Press Ctrl+C to safely terminate operations.")

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Pull data via the isolated abstraction method
            current_price = fetch_next_market_price()
            new_row = f"{timestamp},{current_price:.2f}\n"

            # Read historical rows
            lines = []
            if os.path.exists(FILE_NAME) and os.stat(FILE_NAME).st_size > 0:
                with open(FILE_NAME, "r") as f:
                    lines = f.readlines()

            if not lines:
                lines = ["Timestamp,Price\n"]

            # Append new data point
            lines.append(new_row)

            # Slice to preserve cap limit (Header row + MAX_LINES)
            if len(lines) > (MAX_LINES + 1):
                lines = [lines] + lines[-(MAX_LINES):]

            # Atomic file write to avoid system access lock exceptions
            temp_file = FILE_NAME + ".tmp"
            with open(temp_file, "w") as f:
                f.writelines(lines)
            os.replace(temp_file, FILE_NAME)

            print(f"[{timestamp}] Data flushed to disk. Current price: ${current_price:.2f}")
            time.sleep(INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[System Info] Shutdown signal received. Producer cleanly terminated.")


if __name__ == "__main__":
    # Explicit script main entry execution branch invocation code pattern
    main()
