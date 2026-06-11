"""
Twenty-signal technical strategy for Week 7.

This strategy combines momentum-following and mean-reversion signals calculated
from order book mid prices. TradingEngine owns connectivity, order routing,
position/PnL, risk, dashboard publishing, and kill-switch checks; this class
owns only signal calculation and target-position decisions.
"""

from __future__ import annotations

from collections import deque
import logging
import math
import time
from typing import TYPE_CHECKING

from common.interface_book import VenueOrderBook
from common.interface_order import OrderEvent, Side
from common.interface_trade import AggTrade

if TYPE_CHECKING:
    from trading_engine import TradingEngine


class TwentySignalTechnicalStrategy:

    def __init__(
        self,
        name: str = "TwentySignalTechnicalStrategy",
        history_size: int = 240,
        signal_window_size: int = 20,
        trade_quantity: float = 0.001,
        entry_score: int = 5,
        exit_score: int = 2,
        min_trade_interval_seconds: float = 5.0,
        log_interval_seconds: float = 1.0,
        trade_on_first_signal: bool = False,
    ) -> None:
        if signal_window_size < 20:
            raise ValueError("signal_window_size must be at least 20")
        if history_size < signal_window_size:
            raise ValueError("history_size must be at least signal_window_size")
        if trade_quantity <= 0:
            raise ValueError("trade_quantity must be positive")
        if entry_score <= exit_score:
            raise ValueError("entry_score must be larger than exit_score")

        self.name: str = name
        self.history_size: int = history_size
        self.signal_window_size: int = signal_window_size
        self.trade_quantity: float = trade_quantity
        self.entry_score: int = entry_score
        self.exit_score: int = exit_score
        self.min_trade_interval_seconds: float = min_trade_interval_seconds
        self.log_interval_seconds: float = log_interval_seconds
        self.trade_on_first_signal: bool = trade_on_first_signal

        self.trading_engine: TradingEngine | None = None
        self.mid_prices: dict[str, deque[float]] = {}
        self.last_target_signal: dict[str, int] = {}
        self.last_trade_time: dict[str, float] = {}
        self.last_log_time: dict[str, float] = {}
        self.has_pending_order: dict[str, bool] = {}

    def set_trading_engine(self, trading_engine: TradingEngine) -> None:
        self.trading_engine = trading_engine

    def on_orderbook(self, venue_order_book: VenueOrderBook) -> None:
        if self.trading_engine is None:
            return

        book = venue_order_book.get_book()
        symbol = book.contract_name
        mid_price = (book.get_best_bid() + book.get_best_ask()) / 2.0

        if symbol not in self.mid_prices:
            self.mid_prices[symbol] = deque(maxlen=self.history_size)

        prices = self.mid_prices[symbol]
        prices.append(mid_price)

        if len(prices) < self.signal_window_size:
            self._publish_warmup(symbol, mid_price, len(prices))
            self._log_warmup(symbol, len(prices))
            return

        signals = self._calculate_signals(list(prices))
        momentum_score = sum(signal["vote"] for signal in signals if signal["group"] == "momentum")
        reversal_score = sum(signal["vote"] for signal in signals if signal["group"] == "reversal")
        combined_score = momentum_score + reversal_score
        target_signal = self._score_to_target_signal(symbol, combined_score)
        current_position = self.trading_engine.get_position(symbol)
        target_position = target_signal * self.trade_quantity

        self.trading_engine.update_strategy_analytics(
            {
                "strategy": self.name,
                "symbol": symbol,
                "mid_price": mid_price,
                "momentum_score": momentum_score,
                "reversal_score": reversal_score,
                "combined_score": combined_score,
                "signal": self._format_signal(target_signal),
                "current_position": current_position,
                "target_position": target_position,
                "active_signals": self._format_active_signals(signals),
                "window": f"{len(prices)}/{self.history_size}",
            }
        )

        self._log_signal_state(symbol, mid_price, momentum_score, reversal_score, combined_score, target_signal)
        self._trade_to_target(symbol, target_signal)

    def on_agg_trade(self, trade: AggTrade) -> None:
        pass

    def on_execution(self, order_event: OrderEvent) -> None:
        terminal_status_names = {
            "FILLED",
            "CANCELED",
            "FAILED",
            "EXPIRED",
            "EXPIRED_IN_MATCH",
        }

        if order_event.status.name in terminal_status_names:
            self.has_pending_order[order_event.contract_name] = False

    def _calculate_signals(self, prices: list[float]) -> list[dict]:
        current = prices[-1]
        returns = self._returns(prices)

        sma_10 = self._average(prices[-10:])
        sma_20 = self._average(prices[-20:])
        sma_50 = self._average(prices[-50:])
        sma_100 = self._average(prices[-100:])
        ema_12 = self._ema(prices[-80:], 12)
        ema_26 = self._ema(prices[-80:], 26)
        ema_50 = self._ema(prices[-100:], 50)
        macd_now = ema_12 - ema_26
        macd_prev = self._ema(prices[-81:-1], 12) - self._ema(prices[-81:-1], 26)
        vol_20 = self._stddev(returns[-20:]) or 0.000001
        vol_60 = self._stddev(returns[-60:]) or vol_20
        rsi_14 = self._rsi(prices, 14)
        rsi_7 = self._rsi(prices, 7)
        z_20 = self._z_score(current, prices[-20:])
        z_50 = self._z_score(current, prices[-50:])
        stochastic_14 = self._stochastic(prices[-14:])
        williams_14 = self._williams_r(prices[-14:])
        upper_20, lower_20 = self._bollinger_bands(prices[-20:], 2.0)
        upper_50, lower_50 = self._bollinger_bands(prices[-50:], 2.0)

        signals = [
            self._signal("mom_ema_12_26", "momentum", ema_12 > ema_26, ema_12 < ema_26),
            self._signal("mom_sma_10_50", "momentum", sma_10 > sma_50, sma_10 < sma_50),
            self._signal("mom_price_sma_20", "momentum", current > sma_20, current < sma_20),
            self._signal("mom_price_sma_100", "momentum", current > sma_100, current < sma_100),
            self._signal("mom_5_return", "momentum", self._return_over(prices, 5) > vol_20, self._return_over(prices, 5) < -vol_20),
            self._signal("mom_20_roc", "momentum", self._return_over(prices, 20) > 2 * vol_20, self._return_over(prices, 20) < -2 * vol_20),
            self._signal("mom_macd", "momentum", macd_now > 0, macd_now < 0),
            self._signal("mom_macd_rising", "momentum", macd_now > macd_prev, macd_now < macd_prev),
            self._signal("mom_slope_30", "momentum", self._linear_slope(prices[-30:]) > 0, self._linear_slope(prices[-30:]) < 0),
            self._signal("mom_breakout_60", "momentum", current >= max(prices[-61:-1]), current <= min(prices[-61:-1])),
            self._signal("rev_rsi_14", "reversal", rsi_14 < 30, rsi_14 > 70),
            self._signal("rev_rsi_7", "reversal", rsi_7 < 25, rsi_7 > 75),
            self._signal("rev_z_20", "reversal", z_20 < -2.0, z_20 > 2.0),
            self._signal("rev_z_50", "reversal", z_50 < -2.0, z_50 > 2.0),
            self._signal("rev_bollinger_20", "reversal", current < lower_20, current > upper_20),
            self._signal("rev_bollinger_50", "reversal", current < lower_50, current > upper_50),
            self._signal("rev_stochastic_14", "reversal", stochastic_14 < 20, stochastic_14 > 80),
            self._signal("rev_williams_14", "reversal", williams_14 < -80, williams_14 > -20),
            self._signal("rev_ema_50_extension", "reversal", (current - ema_50) / ema_50 < -2 * vol_60, (current - ema_50) / ema_50 > 2 * vol_60),
            self._signal("rev_3_bar_stretch", "reversal", self._three_bar_stretch(returns) < -3 * vol_20, self._three_bar_stretch(returns) > 3 * vol_20),
        ]

        return signals

    def _score_to_target_signal(self, symbol: str, score: int) -> int:
        previous = self.last_target_signal.get(symbol)

        if score >= self.entry_score:
            target_signal = 1
        elif score <= -self.entry_score:
            target_signal = -1
        elif abs(score) <= self.exit_score:
            target_signal = 0
        else:
            target_signal = previous or 0

        if previous is None:
            self.last_target_signal[symbol] = target_signal
            if not self.trade_on_first_signal:
                return 0

        self.last_target_signal[symbol] = target_signal
        return target_signal

    def _trade_to_target(self, symbol: str, target_signal: int) -> None:
        if self.trading_engine is None:
            return

        if self.has_pending_order.get(symbol, False):
            return

        now = time.time()
        if now - self.last_trade_time.get(symbol, 0.0) < self.min_trade_interval_seconds:
            return

        target_position = target_signal * self.trade_quantity
        current_position = self.trading_engine.get_position(symbol)
        order_quantity = target_position - current_position

        if abs(order_quantity) < 0.00000001:
            return

        side = Side.BUY if order_quantity > 0 else Side.SELL
        quantity = abs(order_quantity)

        logging.info(
            "[%s] target trade | %s %s %.6f current_position=%.6f target_position=%.6f",
            self.name,
            symbol,
            side.name,
            quantity,
            current_position,
            target_position,
        )

        order_sent = self.trading_engine.place_market_order(
            symbol=symbol,
            side=side,
            quantity=quantity,
        )
        self.has_pending_order[symbol] = order_sent

        if order_sent:
            self.last_trade_time[symbol] = now

    def _publish_warmup(self, symbol: str, mid_price: float, current_size: int) -> None:
        if self.trading_engine is None:
            return

        self.trading_engine.update_strategy_analytics(
            {
                "strategy": self.name,
                "symbol": symbol,
                "mid_price": mid_price,
                "signal": "WARMING_UP",
                "window": f"{current_size}/{self.signal_window_size}",
            }
        )

    def _log_warmup(self, symbol: str, current_size: int) -> None:
        now = time.time()
        if now - self.last_log_time.get(symbol, 0.0) < self.log_interval_seconds:
            return

        self.last_log_time[symbol] = now
        logging.info(
            "[%s] Waiting for technical signal window | %s %s/%s",
            self.name,
            symbol,
            current_size,
            self.signal_window_size,
        )

    def _log_signal_state(
        self,
        symbol: str,
        mid_price: float,
        momentum_score: int,
        reversal_score: int,
        combined_score: int,
        target_signal: int,
    ) -> None:
        now = time.time()
        if now - self.last_log_time.get(symbol, 0.0) < self.log_interval_seconds:
            return

        self.last_log_time[symbol] = now
        logging.info(
            "[%s] %s mid=%.2f momentum=%s reversal=%s combined=%s target=%s",
            self.name,
            symbol,
            mid_price,
            momentum_score,
            reversal_score,
            combined_score,
            self._format_signal(target_signal),
        )

    def _signal(self, name: str, group: str, bullish: bool, bearish: bool) -> dict:
        vote = 0
        if bullish and not bearish:
            vote = 1
        elif bearish and not bullish:
            vote = -1

        return {"name": name, "group": group, "vote": vote}

    def _format_active_signals(self, signals: list[dict]) -> str:
        active = [f"{signal['name']}:{signal['vote']:+d}" for signal in signals if signal["vote"] != 0]
        return ", ".join(active)

    def _format_signal(self, signal: int) -> str:
        if signal > 0:
            return "LONG"
        if signal < 0:
            return "SHORT"
        return "FLAT"

    def _average(self, values: list[float]) -> float:
        return sum(values) / len(values)

    def _stddev(self, values: list[float]) -> float:
        if len(values) < 2:
            return 0.0

        mean = self._average(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        return math.sqrt(variance)

    def _ema(self, values: list[float], period: int) -> float:
        multiplier = 2.0 / (period + 1)
        ema = values[0]

        for value in values[1:]:
            ema = value * multiplier + ema * (1 - multiplier)

        return ema

    def _returns(self, prices: list[float]) -> list[float]:
        return [
            (prices[index] / prices[index - 1]) - 1
            for index in range(1, len(prices))
            if prices[index - 1] != 0
        ]

    def _return_over(self, prices: list[float], lookback: int) -> float:
        if len(prices) <= lookback or prices[-lookback - 1] == 0:
            return 0.0

        return (prices[-1] / prices[-lookback - 1]) - 1

    def _linear_slope(self, values: list[float]) -> float:
        n = len(values)
        x_mean = (n - 1) / 2.0
        y_mean = self._average(values)
        numerator = sum((index - x_mean) * (value - y_mean) for index, value in enumerate(values))
        denominator = sum((index - x_mean) ** 2 for index in range(n))

        if denominator == 0:
            return 0.0

        return numerator / denominator

    def _rsi(self, prices: list[float], period: int) -> float:
        changes = [prices[index] - prices[index - 1] for index in range(len(prices) - period, len(prices))]
        gains = [change for change in changes if change > 0]
        losses = [-change for change in changes if change < 0]
        average_gain = sum(gains) / period
        average_loss = sum(losses) / period

        if average_loss == 0:
            return 100.0

        relative_strength = average_gain / average_loss
        return 100.0 - (100.0 / (1.0 + relative_strength))

    def _z_score(self, value: float, sample: list[float]) -> float:
        standard_deviation = self._stddev(sample)
        if standard_deviation == 0:
            return 0.0

        return (value - self._average(sample)) / standard_deviation

    def _stochastic(self, sample: list[float]) -> float:
        low = min(sample)
        high = max(sample)

        if high == low:
            return 50.0

        return ((sample[-1] - low) / (high - low)) * 100.0

    def _williams_r(self, sample: list[float]) -> float:
        low = min(sample)
        high = max(sample)

        if high == low:
            return -50.0

        return -100.0 * (high - sample[-1]) / (high - low)

    def _bollinger_bands(self, sample: list[float], deviations: float) -> tuple[float, float]:
        mean = self._average(sample)
        standard_deviation = self._stddev(sample)
        return mean + deviations * standard_deviation, mean - deviations * standard_deviation

    def _three_bar_stretch(self, returns: list[float]) -> float:
        if len(returns) < 3:
            return 0.0

        return sum(returns[-3:])
