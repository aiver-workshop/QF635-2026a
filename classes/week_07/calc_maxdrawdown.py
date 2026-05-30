import pandas as pd

def max_drawdown(equity_curve):
    equity = pd.Series(equity_curve)

    running_peak = equity.cummax()
    drawdown = (equity - running_peak) / running_peak

    max_dd = drawdown.min()
    end = drawdown.idxmin()
    start = equity[:end + 1].idxmax()

    return {
        "max_drawdown": max_dd,
        "max_drawdown_pct": max_dd * 100,
        "peak_index": start,
        "trough_index": end,
        "peak_value": equity[start],
        "trough_value": equity[end],
    }

# Example
equity_curve = [100, 110, 120, 105, 95, 130, 125, 90, 140]

result = max_drawdown(equity_curve)
print(result)