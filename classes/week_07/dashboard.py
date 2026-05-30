"""
Live Week 7 strategy dashboard.

Reads dashboard_state.json written by SimpleStrategy and displays portfolio
equity plus live position mark-to-market data.
"""

import json
from pathlib import Path

from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go


DASHBOARD_FILE = Path(__file__).with_name("dashboard_state.json")
UPDATE_INTERVAL_MS = 1000

app = Dash(__name__)

BG_COLOR = "#0B0F19"       # Deep cosmic midnight blue canvas
PANEL_COLOR = "#151D30"    # Slightly lighter navy for cards and panels
TEXT_MAIN = "#F1F5F9"      # Clean, crisp slate-white for visibility
TEXT_MUTED = "#94A3B8"     # Soft grey-blue for secondary labels
GRID_COLOR = "#1E293B"     # Muted border lines that separate elements smoothly
ACCENT = "#38BDF8"         # Vibrant ice blue for highlights and focal points
POSITIVE = "#34D399"       # Crisp emerald green for positive returns
NEGATIVE = "#FB7185"       # Sophisticated rose red for negative metrics

CARD_STYLE = {
    "background-color": PANEL_COLOR,
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


def load_state() -> dict:
    if not DASHBOARD_FILE.exists() or DASHBOARD_FILE.stat().st_size == 0:
        return {
            "timestamp": "-",
            "summary": {},
            "positions": [],
        }

    try:
        with open(DASHBOARD_FILE, "r") as file:
            return json.load(file)
    except Exception:
        return {
            "timestamp": "READ_ERROR",
            "summary": {},
            "positions": [],
        }


def format_money(value: float) -> str:
    return f"{value:,.2f}"


def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def metric_card(label: str, value_id: str):
    return html.Div(
        style=CARD_STYLE,
        children=[
            html.Div(
                label,
                style={
                    "color": TEXT_MUTED,
                    "fontSize": "12px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.04em",
                },
            ),
            html.Div(
                id=value_id,
                style={
                    "color": TEXT_MAIN,
                    "fontSize": "24px",
                    "fontWeight": "700",
                },
            ),
        ],
    )


app.layout = html.Div(
    style={
        "backgroundColor": BG_COLOR,
        "minHeight": "100vh",
        "padding": "24px",
        "fontFamily": "Segoe UI, Arial, sans-serif",
        "color": TEXT_MAIN,
    },
    children=[
        html.Div(
            style={"maxWidth": "1180px", "margin": "0 auto"},
            children=[
                html.Div(
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "alignItems": "baseline",
                        "marginBottom": "16px",
                    },
                    children=[
                        html.H1(
                            "Week 7 Strategy Dashboard",
                            style={"fontSize": "26px", "margin": "0"},
                        ),
                        html.Div(
                            id="last-update",
                            style={"color": TEXT_MUTED, "fontSize": "13px"},
                        ),
                    ],
                ),
                html.Div(
                    style={
                        "display": "flex",
                        "gap": "12px",
                        "marginBottom": "16px",
                        "flexWrap": "wrap",
                    },
                    children=[
                        metric_card("Equity", "equity-card"),
                        metric_card("Total PnL", "total-pnl-card"),
                        metric_card("Realized PnL", "realized-pnl-card"),
                        metric_card("Unrealized PnL", "unrealized-pnl-card"),
                        metric_card("Max Drawdown", "max-dd-card"),
                        metric_card("Max Drawdown %", "max-dd-pct-card"),
                    ],
                ),
                html.Div(
                    style={
                        "backgroundColor": PANEL_COLOR,
                        "border": f"1px solid {GRID_COLOR}",
                        "borderRadius": "8px",
                        "padding": "14px",
                    },
                    children=[
                        html.H2(
                            "Live Positions",
                            style={"fontSize": "18px", "margin": "0 0 10px 0"},
                        ),
                        dcc.Graph(
                            id="positions-table",
                            config={"displayModeBar": False},
                            style={"height": "360px"},
                        ),
                    ],
                ),
                dcc.Interval(
                    id="interval-trigger",
                    interval=UPDATE_INTERVAL_MS,
                    n_intervals=0,
                ),
            ],
        )
    ],
)


@app.callback(
    [
        Output("last-update", "children"),
        Output("equity-card", "children"),
        Output("total-pnl-card", "children"),
        Output("realized-pnl-card", "children"),
        Output("unrealized-pnl-card", "children"),
        Output("max-dd-card", "children"),
        Output("max-dd-pct-card", "children"),
        Output("positions-table", "figure"),
    ],
    Input("interval-trigger", "n_intervals"),
)
def update_dashboard(_):
    state = load_state()
    summary = state.get("summary", {})
    positions = state.get("positions", [])

    equity = summary.get("equity", 0.0)
    total_pnl = summary.get("total_pnl", 0.0)
    realized_pnl = summary.get("realized_pnl", 0.0)
    unrealized_pnl = summary.get("unrealized_pnl", 0.0)
    max_drawdown = summary.get("max_drawdown", 0.0)
    max_drawdown_pct = summary.get("max_drawdown_pct", 0.0)

    table = build_positions_table(positions)

    return (
        f"Last update: {state.get('timestamp', '-')}",
        format_money(equity),
        format_money(total_pnl),
        format_money(realized_pnl),
        format_money(unrealized_pnl),
        format_money(max_drawdown),
        format_pct(max_drawdown_pct),
        table,
    )


def build_positions_table(positions: list[dict]):
    columns = [
        "symbol",
        "position",
        "average_entry_price",
        "mark_price",
        "realized_pnl",
        "unrealized_pnl",
        "symbol_pnl",
    ]

    if not positions:
        df = pd.DataFrame([{column: "-" for column in columns}])
    else:
        df = pd.DataFrame(positions)
        for column in columns:
            if column not in df.columns:
                df[column] = 0.0
        df = df[columns]

    display_names = [
        "Symbol",
        "Position",
        "Entry Price",
        "MTM Price",
        "Realized PnL",
        "Unrealized PnL",
        "Symbol PnL",
    ]

    values = []
    for column in columns:
        if column == "symbol":
            values.append(df[column].tolist())
        else:
            values.append([format_table_number(value) for value in df[column]])

    fig = go.Figure(
        data=[
            go.Table(
                header={
                    "values": display_names,
                    "fill_color": GRID_COLOR,  # Deep background for header row contrast
                    "align": "left",
                    "font": {"color": TEXT_MAIN, "size": 13},
                    "line": {"color": GRID_COLOR, "width": 1},
                    "height": 32,
                },
                cells={
                    "values": values,
                    "fill_color": PANEL_COLOR,  # Matching card backgrounds
                    "align": "left",
                    "font": {"color": TEXT_MAIN, "size": 13},
                    "line": {"color": GRID_COLOR, "width": 1},
                    "height": 30,
                },
            )
        ]
    )
    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor=PANEL_COLOR,
    )
    return fig


def format_table_number(value):
    if value == "-":
        return value

    try:
        return f"{float(value):,.6f}"
    except Exception:
        return value


if __name__ == "__main__":
    app.run(debug=False, port=8052)
