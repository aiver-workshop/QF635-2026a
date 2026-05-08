"""
================================================================================
SCRIPT: server_final.py
ROLE: Central Data Broker (REST API Middleware)
DESIGN:
    - Acts as an abstraction layer between raw storage on disk and the dashboard UI.
    - Parses the generated CSV file safely into structured JSON objects.
    - Exposes an HTTP GET endpoint (`/get-stock-data`) for data decoupling.
    - Minimizes parsing errors or file system locks inside the visualization layer.
DEPENDENCIES: fastapi, uvicorn, pandas
================================================================================
"""

import os
import uvicorn
from fastapi import FastAPI
import pandas as pd

app = FastAPI(title="File Broker Service")
FILE_NAME = "realtime_stock_prices.csv"


@app.get("/get-stock-data")
def read_local_file():
    # Structural checks for physical file existence
    if not os.path.exists(FILE_NAME) or os.stat(FILE_NAME).st_size == 0:
        return {"status": "empty", "data": []}

    try:
        # Load CSV structure safely into DataFrame memory space
        df = pd.read_csv(FILE_NAME)
        # Convert matrix collection directly to dictionary schemas
        records = df.to_dict(orient="records")
        return {"status": "active", "data": records}
    except Exception as e:
        return {"status": "error", "message": str(e), "data": []}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
