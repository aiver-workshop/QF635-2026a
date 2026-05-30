"""
Live Week 7 strategy dashboard.
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

    if force_negative and numeric_value != 0:
        color = NEGATIVE
    else:
        color = signal_color(numeric_value)

    return {
        "color": color,
        "fontSize": "32px",
        "fontWeight": "700",
    }


def load_state() -> dict:
    if not DASHBOARD_FILE.exists() or DASHBOARD_FILE.stat().st_size == 0:
        return {"timestamp": "-", "summary": {}, "positions": []}

    try:
        with open(DASHBOARD_FILE, "r") as file:
            return json.load(file)
    except Exception:
        return {"timestamp": "READ_ERROR", "summary": {}, "positions": []}


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
                    },
                    children=[
                        html.H2(
                            "Live Positions",
                            style={"fontSize": "18px", "margin": "0 0 10px 0"},
                        ),
                        dcc.Graph(
                            id="positions-table",
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
        Output("equity-card", "children"),
        Output("total-pnl-card", "children"),
        Output("realized-pnl-card", "children"),
        Output("unrealized-pnl-card", "children"),
        Output("max-dd-card", "children"),
        Output("max-dd-pct-card", "children"),
        Output("positions-table", "figure"),

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
                    "font": {
                        "color": TEXT_MAIN,
                        "size": 15,
                    },
                    "line": {
                        "color": GRID_COLOR,
                        "width": 1,
                    },
                    "height": 40,
                },
                cells={
                    "values": values,
                    "fill_color": PANEL_COLOR,
                    "align": alignments,
                    "font": {
                        "color": font_colors,
                        "size": 16,
                    },
                    "line": {
                        "color": GRID_COLOR,
                        "width": 1,
                    },
                    "height": 38,
                }
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


if __name__ == "__main__":
    app.run(debug=False, port=8052)