import json
import time
from pathlib import Path

from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.graph_objects as go


DASHBOARD_FILE = Path(__file__).with_name("dashboard_state.json")
UPDATE_INTERVAL_MS = 1000
STALE_AFTER_SECONDS = 5

last_seen_timestamp = None
last_change_time = time.time()

app = Dash(__name__)

app.index_string = """
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
        @keyframes flash {
            0% { opacity: 1; }
            50% { opacity: 0.25; }
            100% { opacity: 1; }
        }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>
        {%config%}
        {%scripts%}
        {%renderer%}
    </footer>
</body>
</html>
"""

BG_COLOR = "#0B0F19"
PANEL_COLOR = "#151D30"
HEADER_COLOR = "#202B3D"
TEXT_MAIN = "#F1F5F9"
TEXT_MUTED = "#94A3B8"
GRID_COLOR = "#1E293B"
POSITIVE = "#4ADE80"
NEGATIVE = "#F87171"
EQUITY_ACCENT = "#3B82F6"

CARD_STYLE = {
    "backgroundColor": PANEL_COLOR,
    "color": TEXT_MAIN,
    "padding": "20px",
    "borderRadius": "12px",
    "textAlign": "center",
    "flex": "1",
    "margin": "10px",
    "boxShadow": "0 10px 15px -3px rgba(0,0,0,0.3)",
    "fontFamily": "Segoe UI, -apple-system, Arial",
    "border": "1px solid #334155",
}


def signal_color(value):
    try:
        value = float(value)
        if value > 0:
            return POSITIVE
        if value < 0:
            return NEGATIVE
    except Exception:
        pass
    return TEXT_MAIN


def get_equity_card_style():
    style = CARD_STYLE.copy()
    style["borderTop"] = f"3px solid {EQUITY_ACCENT}"
    style["boxShadow"] = "0 0 12px rgba(59,130,246,0.18)"
    return style


def get_neutral_card_style():
    return CARD_STYLE.copy()


def get_value_style(value, force_negative=False):
    try:
        numeric_value = float(value)
    except Exception:
        numeric_value = 0.0

    color = NEGATIVE if force_negative and numeric_value != 0 else signal_color(numeric_value)

    return {
        "color": color,
        "fontSize": "32px",
        "fontWeight": "700",
    }


def load_state() -> dict:
    if not DASHBOARD_FILE.exists() or DASHBOARD_FILE.stat().st_size == 0:
        return {"timestamp": "-", "summary": {}, "positions": [], "orders": []}

    try:
        with open(DASHBOARD_FILE, "r") as file:
            return json.load(file)
    except Exception:
        return {"timestamp": "READ_ERROR", "summary": {}, "positions": [], "orders": []}


def format_money(value: float) -> str:
    return f"{value:,.2f}"


def format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def metric_card(label: str, value_id: str, card_id: str):
    return html.Div(
        id=card_id,
        style=CARD_STYLE,
        children=[
            html.Div(
                label,
                style={
                    "color": TEXT_MUTED,
                    "fontSize": "11px",
                    "textTransform": "uppercase",
                    "letterSpacing": "0.04em",
                },
            ),
            html.Div(
                id=value_id,
                style={
                    "color": TEXT_MAIN,
                    "fontSize": "32px",
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
                            children=[
                                html.Div(
                                    id="last-update",
                                    style={"color": TEXT_MUTED, "fontSize": "13px"},
                                ),
                                html.Div(
                                    id="stale-alert",
                                    style={"display": "none"},
                                ),
                            ]
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
                        metric_card("Equity", "equity-card", "equity-container"),
                        metric_card("Total PnL", "total-pnl-card", "total-pnl-container"),
                        metric_card("Realized PnL", "realized-pnl-card", "realized-pnl-container"),
                        metric_card("Unrealized PnL", "unrealized-pnl-card", "unrealized-pnl-container"),
                        metric_card("Max Drawdown", "max-dd-card", "max-dd-container"),
                        metric_card("Max Drawdown %", "max-dd-pct-card", "max-dd-pct-container"),
                    ],
                ),
                html.Div(
                    style={
                        "backgroundColor": PANEL_COLOR,
                        "border": f"1px solid {GRID_COLOR}",
                        "borderRadius": "8px",
                        "padding": "14px",
                        "marginBottom": "16px",
                    },
                    children=[
                        html.H2(
                            "Equity Curve",
                            style={"fontSize": "18px", "margin": "0 0 10px 0"},
                        ),
                        dcc.Graph(
                            id="equity-chart",
                            config={"displayModeBar": False},
                            style={"height": "320px"},
                        ),
                    ],
                ),
                html.Div(
                    style={
                        "backgroundColor": PANEL_COLOR,
                        "border": f"1px solid {GRID_COLOR}",
                        "borderRadius": "8px",
                        "padding": "14px",
                        "marginBottom": "16px",
                    },
                    children=[
                        html.H2(
                            "Live Positions",
                            style={"fontSize": "18px", "margin": "0 0 10px 0"},
                        ),
                        dcc.Graph(
                            id="positions-table",
                            config={"displayModeBar": False},
                            style={"height": "220px"},
                        ),
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
                            "Order History",
                            style={"fontSize": "18px", "margin": "0 0 10px 0"},
                        ),
                        dcc.Graph(
                            id="orders-table",
                            config={"displayModeBar": False},
                            style={"height": "420px"},
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
        Output("stale-alert", "children"),
        Output("stale-alert", "style"),

        Output("equity-card", "children"),
        Output("total-pnl-card", "children"),
        Output("realized-pnl-card", "children"),
        Output("unrealized-pnl-card", "children"),
        Output("max-dd-card", "children"),
        Output("max-dd-pct-card", "children"),
        Output("equity-chart", "figure"),
        Output("positions-table", "figure"),
        Output("orders-table", "figure"),

        Output("equity-container", "style"),
        Output("total-pnl-container", "style"),
        Output("realized-pnl-container", "style"),
        Output("unrealized-pnl-container", "style"),
        Output("max-dd-container", "style"),
        Output("max-dd-pct-container", "style"),

        Output("equity-card", "style"),
        Output("total-pnl-card", "style"),
        Output("realized-pnl-card", "style"),
        Output("unrealized-pnl-card", "style"),
        Output("max-dd-card", "style"),
        Output("max-dd-pct-card", "style"),
    ],
    Input("interval-trigger", "n_intervals"),
)
def update_dashboard(_):
    global last_seen_timestamp, last_change_time

    state = load_state()
    current_timestamp = state.get("timestamp", "-")
    now = time.time()

    if current_timestamp != last_seen_timestamp:
        last_seen_timestamp = current_timestamp
        last_change_time = now

    is_stale = now - last_change_time > STALE_AFTER_SECONDS

    stale_style = {
        "display": "block" if is_stale else "none",
        "color": "#EF4444",
        "fontSize": "13px",
        "fontWeight": "700",
        "marginTop": "4px",
        "animation": "flash 1s infinite",
        "textAlign": "right",
    }

    summary = state.get("summary", {})
    positions = state.get("positions", [])
    orders = state.get("orders", [])

    equity = summary.get("equity", 0.0)
    total_pnl = summary.get("total_pnl", 0.0)
    realized_pnl = summary.get("realized_pnl", 0.0)
    unrealized_pnl = summary.get("unrealized_pnl", 0.0)
    max_drawdown = summary.get("max_drawdown", 0.0)
    max_drawdown_pct = summary.get("max_drawdown_pct", 0.0)
    equity_curve = summary.get("equity_curve", [])

    equity_chart = build_equity_chart(equity_curve, equity)
    positions_table = build_positions_table(positions)
    orders_table = build_orders_table(orders)

    return (
        f"Last update: {current_timestamp}",
        "DATA STALE: no update for more than 5 seconds",
        stale_style,

        format_money(equity),
        format_money(total_pnl),
        format_money(realized_pnl),
        format_money(unrealized_pnl),
        format_money(max_drawdown),
        format_pct(max_drawdown_pct),
        equity_chart,
        positions_table,
        orders_table,

        get_equity_card_style(),
        get_neutral_card_style(),
        get_neutral_card_style(),
        get_neutral_card_style(),
        get_neutral_card_style(),
        get_neutral_card_style(),

        get_value_style(equity),
        get_value_style(total_pnl),
        get_value_style(realized_pnl),
        get_value_style(unrealized_pnl),
        get_value_style(max_drawdown, force_negative=True),
        get_value_style(max_drawdown_pct, force_negative=True),
    )


def build_equity_chart(equity_curve: list[float], current_equity: float):
    if not equity_curve:
        equity_curve = [current_equity]

    x_values = list(range(len(equity_curve)))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_values,
            y=equity_curve,
            mode="lines",
            line={"color": EQUITY_ACCENT, "width": 2},
            hovertemplate="Observation %{x}<br>Equity %{y:,.2f}<extra></extra>",
        )
    )

    fig.update_layout(
        margin={"l": 48, "r": 18, "t": 8, "b": 36},
        paper_bgcolor=PANEL_COLOR,
        plot_bgcolor=PANEL_COLOR,
        font={"color": TEXT_MAIN},
        xaxis={
            "title": "Observation",
            "gridcolor": GRID_COLOR,
            "zerolinecolor": GRID_COLOR,
            "color": TEXT_MUTED,
        },
        yaxis={
            "title": "Equity",
            "gridcolor": GRID_COLOR,
            "zerolinecolor": GRID_COLOR,
            "color": TEXT_MUTED,
            "tickformat": ",.2f",
        },
        hovermode="x unified",
    )

    return fig


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
        elif column == "position":
            values.append([format_position(value) for value in df[column]])
        else:
            values.append([format_table_number(value) for value in df[column]])

    font_colors = []
    for column in columns:
        if column in ["position", "realized_pnl", "unrealized_pnl", "symbol_pnl"]:
            font_colors.append([signal_color(v) for v in df[column]])
        elif column == "mark_price":
            font_colors.append(
                [
                    mtm_color(row["position"], row["average_entry_price"], row["mark_price"])
                    for _, row in df.iterrows()
                ]
            )
        else:
            font_colors.append([TEXT_MAIN] * len(df))

    alignments = ["center", "right", "right", "right", "right", "right", "right"]

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[1.0, 1.1, 1.2, 1.2, 1.2, 1.2, 1.2],
                header={
                    "values": display_names,
                    "fill_color": HEADER_COLOR,
                    "align": alignments,
                    "font": {"color": TEXT_MAIN, "size": 15},
                    "line": {"color": GRID_COLOR, "width": 1},
                    "height": 40,
                },
                cells={
                    "values": values,
                    "fill_color": PANEL_COLOR,
                    "align": alignments,
                    "font": {"color": font_colors, "size": 16},
                    "line": {"color": GRID_COLOR, "width": 1},
                    "height": 38,
                },
            )
        ]
    )

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor=PANEL_COLOR,
        plot_bgcolor=PANEL_COLOR,
    )

    return fig


def build_orders_table(orders: list[dict]):
    columns = [
        "created_time",
        "updated_time",
        "symbol",
        "side",
        "status",
        "execution_type",
        "average_filled_price",
        "filled_quantity",
        "order_id",
        "canceled_reason",
    ]

    if not orders:
        df = pd.DataFrame([{column: "-" for column in columns}])
    else:
        df = pd.DataFrame(orders)
        for column in columns:
            if column not in df.columns:
                df[column] = "-"
        df = df[columns].tail(20).iloc[::-1]

    display_names = [
        "Created",
        "Updated",
        "Symbol",
        "Side",
        "Status",
        "Type",
        "Avg Fill",
        "Filled Qty",
        "Order ID",
        "Reason",
    ]

    values = []
    for column in columns:
        if column == "average_filled_price":
            values.append([format_table_number(value) for value in df[column]])
        elif column == "filled_quantity":
            values.append([format_position(value) for value in df[column]])
        elif column == "order_id":
            values.append([format_order_id(value) for value in df[column]])
        else:
            values.append(df[column].tolist())

    font_colors = []
    for column in columns:
        if column == "side":
            font_colors.append([side_color(value) for value in df[column]])
        elif column == "status":
            font_colors.append([status_color(value) for value in df[column]])
        else:
            font_colors.append([TEXT_MAIN] * len(df))

    alignments = ["center", "center", "center", "center", "center", "center", "right", "right", "center", "center"]

    fig = go.Figure(
        data=[
            go.Table(
                columnwidth=[0.8, 0.8, 1.0, 0.7, 1.2, 1.1, 1.1, 1.0, 1.6, 1.1],
                header={
                    "values": display_names,
                    "fill_color": HEADER_COLOR,
                    "align": alignments,
                    "font": {"color": TEXT_MAIN, "size": 14},
                    "line": {"color": GRID_COLOR, "width": 1},
                    "height": 40,
                },
                cells={
                    "values": values,
                    "fill_color": PANEL_COLOR,
                    "align": alignments,
                    "font": {"color": font_colors, "size": 14},
                    "line": {"color": GRID_COLOR, "width": 1},
                    "height": 34,
                },
            )
        ]
    )

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        paper_bgcolor=PANEL_COLOR,
        plot_bgcolor=PANEL_COLOR,
    )

    return fig


def mtm_color(position, entry_price, mark_price):
    try:
        position = float(position)
        entry_price = float(entry_price)
        mark_price = float(mark_price)
    except Exception:
        return TEXT_MAIN

    if position > 0:
        if mark_price > entry_price:
            return POSITIVE
        if mark_price < entry_price:
            return NEGATIVE

    if position < 0:
        if mark_price < entry_price:
            return POSITIVE
        if mark_price > entry_price:
            return NEGATIVE

    return TEXT_MAIN


def format_table_number(value):
    if value == "-":
        return value

    try:
        return f"{float(value):,.2f}"
    except Exception:
        return value


def format_position(value):
    if value == "-":
        return value

    try:
        return f"{float(value):,.4f}"
    except Exception:
        return value


def format_order_id(value):
    if value == "-":
        return value

    value = str(value)
    if len(value) <= 14:
        return value

    return f"{value[:6]}...{value[-6:]}"


def side_color(value):
    if value == "BUY":
        return POSITIVE
    if value == "SELL":
        return NEGATIVE

    return TEXT_MAIN


def status_color(value):
    if value in ["FILLED", "PARTIALLY_FILLED"]:
        return POSITIVE
    if value in ["CANCELED", "FAILED", "EXPIRED", "EXPIRED_IN_MATCH"]:
        return NEGATIVE

    return TEXT_MAIN


if __name__ == "__main__":
    app.run(debug=False, port=8052)
