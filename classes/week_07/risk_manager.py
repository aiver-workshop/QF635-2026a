"""
Risk manager for equity-curve based metrics.

PositionManager owns positions and PnL. RiskManager consumes equity updates and
calculates risk/performance measures such as drawdown.
"""


class RiskManager:

    def __init__(self):
        self.equity_curve = []
        self.peak_equity = None
        self.current_drawdown = 0.0
        self.current_drawdown_pct = 0.0
        self.max_drawdown = 0.0
        self.max_drawdown_pct = 0.0

    def on_equity_update(self, equity: float) -> None:
        self.equity_curve.append(equity)

        if self.peak_equity is None or equity > self.peak_equity:
            self.peak_equity = equity

        self.current_drawdown = equity - self.peak_equity
        self.current_drawdown_pct = self._calculate_drawdown_pct(
            drawdown=self.current_drawdown,
            peak_equity=self.peak_equity,
        )

        if self.current_drawdown < self.max_drawdown:
            self.max_drawdown = self.current_drawdown
            self.max_drawdown_pct = self.current_drawdown_pct

    def get_current_drawdown(self) -> float:
        return self.current_drawdown

    def get_current_drawdown_pct(self) -> float:
        return self.current_drawdown_pct

    def get_max_drawdown(self) -> float:
        return self.max_drawdown

    def get_max_drawdown_pct(self) -> float:
        return self.max_drawdown_pct

    def get_peak_equity(self) -> float:
        if self.peak_equity is None:
            return 0.0

        return self.peak_equity

    def get_latest_equity(self) -> float:
        if not self.equity_curve:
            return 0.0

        return self.equity_curve[-1]

    def _calculate_drawdown_pct(self, drawdown: float, peak_equity: float) -> float:
        if peak_equity == 0:
            return 0.0

        return drawdown / peak_equity


if __name__ == "__main__":
    risk_manager = RiskManager()
    test_equity_curve = [0.0, 10.0, 7.0, 12.0, 4.0, 9.0]

    for equity in test_equity_curve:
        risk_manager.on_equity_update(equity)
        print(
            "equity =",
            equity,
            "peak =",
            risk_manager.get_peak_equity(),
            "current_drawdown =",
            risk_manager.get_current_drawdown(),
            "current_drawdown_pct =",
            risk_manager.get_current_drawdown_pct(),
            "max_drawdown =",
            risk_manager.get_max_drawdown(),
            "max_drawdown_pct =",
            risk_manager.get_max_drawdown_pct(),
        )
