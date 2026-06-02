"""
Draw the event-driven pair backtesting design as a PNG.

Run:
    py draw_event_driven_backtest_design.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


CURRENT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = CURRENT_DIR / "diagrams"
OUTPUT_FILE = OUTPUT_DIR / "event_driven_backtest_design.png"


BOX_STYLE = {
    "boxstyle": "round,pad=0.03,rounding_size=0.03",
    "linewidth": 1.8,
    "edgecolor": "#334155",
}


def add_box(ax, xy, width, height, title, body, facecolor):
    x, y = xy
    box = FancyBboxPatch(
        (x, y),
        width,
        height,
        facecolor=facecolor,
        **BOX_STYLE,
    )
    ax.add_patch(box)
    ax.text(
        x + width / 2,
        y + height - 0.24,
        title,
        ha="center",
        va="top",
        fontsize=13,
        color="#F8FAFC",
        weight="bold",
    )
    ax.text(
        x + width / 2,
        y + height / 2 - 0.12,
        body,
        ha="center",
        va="center",
        fontsize=9.5,
        color="#D7E3F4",
        linespacing=1.25,
    )


def add_arrow(ax, start, end, label, color="#60A5FA", curve=0.0):
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=18,
        linewidth=2.0,
        color=color,
        connectionstyle=f"arc3,rad={curve}",
    )
    ax.add_patch(arrow)

    mid_x = (start[0] + end[0]) / 2
    mid_y = (start[1] + end[1]) / 2
    ax.text(
        mid_x,
        mid_y + 0.14,
        label,
        ha="center",
        va="center",
        fontsize=9,
        color=color,
        weight="bold",
        bbox={
            "boxstyle": "round,pad=0.22",
            "facecolor": "#0B1120",
            "edgecolor": "none",
            "alpha": 0.9,
        },
    )


def draw_diagram():
    fig, ax = plt.subplots(figsize=(15, 9), dpi=160)
    fig.patch.set_facecolor("#0B1120")
    ax.set_facecolor("#0B1120")
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 9)
    ax.axis("off")

    ax.text(
        7.5,
        8.55,
        "Event-Driven Pair Backtesting Design",
        ha="center",
        va="center",
        fontsize=22,
        color="#F8FAFC",
        weight="bold",
    )
    ax.text(
        7.5,
        8.15,
        "The strategy uses the same TradingEngine API as live trading; only the gateway and order manager are simulated.",
        ha="center",
        va="center",
        fontsize=11,
        color="#CBD5E1",
    )

    add_box(
        ax,
        (0.7, 6.0),
        2.7,
        1.35,
        "CSV Market Data",
        "BTCUSDT / ETHUSDT\n1-second prices",
        "#1D4ED8",
    )
    add_box(
        ax,
        (4.1, 6.0),
        3.0,
        1.35,
        "SimulatedGateway",
        "replays order books\nemits callbacks\ncreates simulated fills",
        "#0F766E",
    )
    add_box(
        ax,
        (8.0, 6.0),
        3.0,
        1.35,
        "TradingEngine",
        "routes callbacks\nupdates PnL / risk\nrecords orders",
        "#7C3AED",
    )
    add_box(
        ax,
        (12.0, 6.0),
        2.8,
        1.35,
        "PairTradingStrategy",
        "spread window\nz-score signal\ntarget pair state",
        "#B45309",
    )

    add_box(
        ax,
        (4.1, 3.45),
        3.0,
        1.35,
        "SimulatorOrderManager",
        "checks notional\nroutes order to simulator",
        "#0E7490",
    )
    add_box(
        ax,
        (8.0, 3.45),
        3.0,
        1.35,
        "PositionManager",
        "fills -> position\navg entry\nrealized / unrealized PnL",
        "#166534",
    )
    add_box(
        ax,
        (12.0, 3.45),
        2.8,
        1.35,
        "RiskManager",
        "equity curve\ndrawdown\nrisk metrics",
        "#BE123C",
    )

    add_box(
        ax,
        (8.0, 1.0),
        3.0,
        1.25,
        "End-of-Run Report",
        "final equity\nPnL\npositions\norder history",
        "#475569",
    )

    add_arrow(ax, (3.4, 6.68), (4.1, 6.68), "load rows")
    add_arrow(ax, (7.1, 6.68), (8.0, 6.68), "on_orderbook")
    add_arrow(ax, (11.0, 6.68), (12.0, 6.68), "strategy callback")

    add_arrow(
        ax,
        (12.0, 6.25),
        (7.1, 4.15),
        "place_market_order",
        color="#FBBF24",
        curve=0.18,
    )
    add_arrow(ax, (4.1, 4.15), (4.1, 5.95), "simulated order", color="#FBBF24")
    add_arrow(
        ax,
        (5.6, 5.95),
        (8.0, 6.2),
        "execution fill",
        color="#34D399",
        curve=-0.18,
    )

    add_arrow(ax, (9.5, 5.95), (9.5, 4.8), "on_fill", color="#34D399")
    add_arrow(ax, (11.0, 4.15), (12.0, 4.15), "equity update", color="#FB7185")
    add_arrow(ax, (9.5, 3.45), (9.5, 2.25), "snapshot", color="#A5B4FC")
    add_arrow(ax, (13.4, 3.45), (11.0, 1.65), "risk snapshot", color="#A5B4FC")

    ax.text(
        0.85,
        0.55,
        "Key idea: event-driven backtesting preserves the live callback shape, while replacing exchange connectivity with simulated market data and fills.",
        ha="left",
        va="center",
        fontsize=11,
        color="#CBD5E1",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_FILE, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved diagram to {OUTPUT_FILE}")


if __name__ == "__main__":
    draw_diagram()
