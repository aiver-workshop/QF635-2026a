"""
Small JSON store for the Week 7 live dashboard.

The trading strategy writes the latest state. The dashboard reads the file on a
timer. This keeps the strategy and UI loosely coupled for teaching purposes.
"""

import json
import os
from datetime import datetime
from pathlib import Path


class DashboardStore:

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def publish(self, summary: dict, positions: list[dict]) -> None:
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": summary,
            "positions": positions,
        }

        temp_path = self.file_path.with_suffix(self.file_path.suffix + ".tmp")
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_path, "w") as file:
            json.dump(payload, file, indent=2)

        os.replace(temp_path, self.file_path)
