"""
================================================================================
SCRIPT: app_fastapi_blue.py
ROLE: Live Dashboard Sourced via FastAPI Microservice (Midnight Blue Theme)
DESIGN:
    - Queries the dedicated web backend (/get-stock-data) over HTTP.
    - Uses app.run() to comply with modern Dash compilation rules.
    - Incorporates neon cyan and warm gold data summary widgets.
    - Completely eliminates disk file access and permission errors in UI thread.
DEPENDENCIES: dash, plotly, pandas, requests
================================================================================
"""

import os
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import requests

# Endpoints configuration - http://127.0.0.1:8000/get-stock-data
API_BASE_URL = "http://127.0.0.1:8000"
DATA_ENDPOINT = "/get-stock-data"
API_ENDPOINT = f"{API_BASE_URL}{DATA_ENDPOINT}"
UPDATE_INTERVAL_MS = 1000

app = Dash(__name__)

# Premium Midnight Blue Color Palette Definitions
BG_COLOR = "#0F172A"  # Deep slate blue canvas background
CARD_COLOR = "#1E293B"  # Dark blue for layout cards
TEXT_MAIN = "#F8FAFC"  # Off-white crisp text
TEXT_MUTED = "#94A3B8"  # Gray-blue secondary text

CARD_STYLE = {
    "background-color": CARD_COLOR,
    "color": TEXT_MAIN,
    "padding": "20px",
    "border-radius": "12px",
    "text-align": "center",
    "flex": "1",
    "margin": "10px",
    "box-shadow": "0 10px 15px -3px rgba(0,0,0,0.3)",
    "fontFamily": "Segoe UI, -apple-system, Arial",
    "border": "1px solid #334155"
}

app.layout = html.Div(
    style={"background-color": BG_COLOR, "padding": "30px", "minHeight": "100vh"},
    children=[
        html.H1(
            "Microservice Trading Stream Analytics",
            style={"textAlign": "center", "fontFamily": "Segoe UI, Arial", "color": TEXT_MAIN, "fontWeight": "600",
                   "marginBottom": "30px"},
        ),

        # High-level metric flex row layout
        html.Div(
            style={"display": "flex", "justify-content": "space-around", "marginBottom": "20px"},
            children=[
                html.Div(
                    style=CARD_STYLE,
                    children=[
                        html.H3("LAST TRADED PRICE", style={"margin": "0", "fontSize": "13px", "color": TEXT_MUTED,
                                                            "letterSpacing": "0.05em"}),
                        html.Div(id="live-price-display",
                                 style={"fontSize": "38px", "fontWeight": "700", "color": "#38BDF8",
                                        "marginTop": "10px"})
                    ]
                ),
                html.Div(
                    style=CARD_STYLE,
                    children=[
                        html.H3("LAST UPDATE TIME", style={"margin": "0", "fontSize": "13px", "color": TEXT_MUTED,
                                                           "letterSpacing": "0.05em"}),
                        html.Div(id="live-time-display",
                                 style={"fontSize": "24px", "fontWeight": "600", "color": "#FBBD23",
                                        "marginTop": "22px"})
                    ]
                )
            ]
        ),

        dcc.Interval(
            id="interval-trigger",
            interval=UPDATE_INTERVAL_MS,
            n_intervals=0,
        ),

        html.Div(
            style={"background-color": CARD_COLOR, "padding": "20px", "border-radius": "12px",
                   "border": "1px solid #334155", "box-shadow": "0 10px 15px -3px rgba(0,0,0,0.3)"},
            children=[dcc.Graph(id="live-stock-graph")]
        ),
    ]
)


@app.callback(
    [
        Output("live-stock-graph", "figure"),
        Output("live-price-display", "children"),
        Output("live-time-display", "children")
    ],
    Input("interval-trigger", "n_intervals"),
)
def update_live_dashboard(n):
    # Blueprint for fallback chart layouts
    error_fig = px.line(title="Awaiting API Service Connection...")
    error_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor=CARD_COLOR,
        font_color=TEXT_MUTED
    )

    try:
        # Pull transactional tracking metrics from the API service
        response = requests.get(API_ENDPOINT, timeout=1.5)
        if response.status_code != 200:
            return px.line(title=f"API Error Code: {response.status_code}"), "API_ERR", "API_ERR"

        payload = response.json()
    except requests.exceptions.RequestException:
        return error_fig, "CONN_ERR", "OFFLINE"

    data_points = payload.get("data", [])

    if not data_points:
        return px.line(title="Syncing pipeline with disk updates..."), "$ --.--", "--:--:--"

    # Construct DataFrame out of memory object records
    df = pd.DataFrame(data_points)

    # Extract metrics from the final dict entry
    last_row = df.iloc[-1]
    last_price = f"${last_row['Price']:.2f}"
    last_time = str(last_row["Timestamp"])

    # Graph canvas construction
    fig = px.line(
        df,
        x="Timestamp",
        y="Price",
        title=f"Active Stream Buffer ({len(df)} ticks)",
    )

    # Blend graphic panel perfectly with the custom midnight blue container cards
    fig.update_layout(
        xaxis_title="Network Timestamp",
        yaxis_title="Price ($)",
        template="plotly_dark",
        plot_bgcolor=CARD_COLOR,
        paper_bgcolor=CARD_COLOR,
        font_color=TEXT_MAIN,
        xaxis=dict(gridcolor="#334155", showgrid=True),
        yaxis=dict(gridcolor="#334155", showgrid=True),
        title=dict(font=dict(size=14, color=TEXT_MUTED))
    )

    # Custom colored tracing line to match the blue layout structure
    fig.update_traces(line=dict(color="#38BDF8", width=2.5))
    fig.update_yaxes(autorange=True)

    return fig, last_price, last_time


if __name__ == "__main__":
    # Correct updated execution configuration block
    app.run(debug=True, port=8051)
