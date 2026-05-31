"""
Small JSON store for the Week 7 live dashboard.

The trading engine writes the latest state. The dashboard reads the file on a
timer. This keeps the strategy and UI loosely coupled for teaching purposes.
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from threading import get_ident


class DashboardStore:

    def __init__(self, file_path: str | Path) -> None:
        self.file_path: Path = Path(file_path)

    def publish(
        self,
        summary: dict,
        positions: list[dict],
        orders: list[dict] | None = None,
        analytics: dict | None = None,
    ) -> None:
        payload = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "summary": summary,
            "positions": positions,
            "orders": orders or [],
            "analytics": analytics or {},
        }

        temp_path = self.file_path.with_suffix(
            f"{self.file_path.suffix}.{os.getpid()}.{get_ident()}.tmp"
        )
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2)

        for attempt in range(3):
            try:
                os.replace(temp_path, self.file_path)
                return
            except PermissionError:
                if attempt == 2:
                    logging.warning(
                        "Could not publish dashboard state because the file is locked: %s",
                        self.file_path,
                    )
                    self._remove_temp_file(temp_path)
                    return

                time.sleep(0.05)

    def _remove_temp_file(self, temp_path: Path) -> None:
        try:
            temp_path.unlink(missing_ok=True)
        except PermissionError:
            pass
