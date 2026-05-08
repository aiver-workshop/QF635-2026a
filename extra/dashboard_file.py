"""
================================================================================
SCRIPT: app_direct_blue.py
ROLE: Live Dashboard with Midnight Blue Theme (Direct File Access)
DESIGN:
    - Implements a modern dark navy/blue financial aesthetic layout.
    - Periodically parses the 1,000-line capped CSV directly from disk.
    - Uses app.run() for modern Dash compatibility.
    - Features matched neon accent card indicators for price and timestamp.
DEPENDENCIES: dash, plotly, pandas
================================================================================
"""

import os
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px

# Configuration
FILE_NAME = "realtime_stock_prices.csv"
UPDATE_INTERVAL_MS = 1000

app = Dash(__name__)

# Premium Midnight Blue Color Palette
BG_COLOR = "#0F172A"  # Deep slate blue canvas background
CARD_COLOR = "#1E293B"  # Slightly lighter dark blue for layout cards
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
            "Live Trading Stream Analytics",
            style={"textAlign": "center", "fontFamily": "Segoe UI, Arial", "color": TEXT_MAIN, "fontWeight": "600",
                   "marginBottom": "30px"},
        ),

        # High-level metric flex container
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
    # Blueprint for chart fallbacks
    error_fig = px.line(title="Waiting for System Sync...")
    error_fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=CARD_COLOR,
        plot_bgcolor=CARD_COLOR,
        font_color=TEXT_MUTED
    )

    if not os.path.exists(FILE_NAME) or os.stat(FILE_NAME).st_size == 0:
        return error_fig, "$ --.--", "--:--:--"

    try:
        df = pd.read_csv(FILE_NAME)
    except PermissionError:
        return error_fig, "LOCKED", "SYNCING"
    except Exception as e:
        return px.line(title=f"Error: {str(e)}"), "ERROR", "ERROR"

    if df.empty:
        return error_fig, "$ --.--", "--:--:--"

    # Metrics mining
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

    # Style graph elements to seamlessly match web frame background
    fig.update_layout(
        xaxis_title="File Timestamp",
        yaxis_title="Price ($)",
        template="plotly_dark",
        plot_bgcolor=CARD_COLOR,  # Background inside graph axes
        paper_bgcolor=CARD_COLOR,  # Background around graph borders
        font_color=TEXT_MAIN,
        xaxis=dict(gridcolor="#334155", showgrid=True),
        yaxis=dict(gridcolor="#334155", showgrid=True),
        title=dict(font=dict(size=16, color=TEXT_MAIN))
    )

    # Custom colored tracing line
    fig.update_traces(line=dict(color="#38BDF8", width=2.5))
    fig.update_yaxes(autorange=True)

    return fig, last_price, last_time


if __name__ == "__main__":
    # Updated invocation execution statement
    app.run(debug=True, port=8050)
