"""
Aggregate trading signals across multiple horizons.

This example combines fast, medium, and slow signals by:
    1. Decaying each signal by age and half-life.
    2. Normalizing the decayed weights.
    3. Computing a combined forecast.
    4. Smoothing the forecast with EWMA.
    5. Applying a threshold and confidence-based position size.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

import pandas as pd


def round_half_up(value: float, decimals: int = 3) -> float:
    """Round the way examples are usually shown in teaching slides."""
    quantizer = Decimal("1").scaleb(-decimals)
    return float(Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP))


class MultiHorizonSignalAggregator:
    def __init__(self, half_lives: dict[str, float], threshold: float = 0.05, alpha: float = 0.2):
        """
        Initialize the signal aggregator.

        :param half_lives: Dict mapping signal names to half-life in minutes.
        :param threshold: Activation threshold for taking a position.
        :param alpha: EWMA smoothing factor for the forecast.
        """
        self.half_lives = half_lives
        self.threshold = threshold
        self.alpha = alpha
        self.prev_smooth_forecast = 0.0

    def _calculate_raw_weights(self, ages: dict[str, float]) -> dict[str, float]:
        """Compute raw decay weights using the 0.5 base formula."""
        raw_weights = {}

        for signal_id, age in ages.items():
            half_life = self.half_lives.get(signal_id)

            if half_life is None:
                raise ValueError(f"Half-life missing for signal: {signal_id}")

            if half_life <= 0:
                raise ValueError(f"Half-life must be positive for signal: {signal_id}")

            # Half-life decay: a signal loses half its weight every half-life period.
            raw_weights[signal_id] = 0.5 ** (age / half_life)

        return raw_weights

    def _confidence_function_linear_with_cap(self, confidence: float, c_max: float = 1.5) -> float:
        """Position sizing multiplier f(C), linear with a cap at c_max."""
        return min(confidence / c_max, 1.0)

    def _calculate_display_normalized_weights(
        self,
        normalized_weights: dict[str, float],
        decimals: int = 3,
    ) -> dict[str, float]:
        """
        Round normalized weights for display while keeping the displayed sum at 1.000.

        The infographic rounds the first weights and makes the final displayed
        weight the remainder, so students see normalized weights that add exactly
        to one.
        """
        signal_ids = list(normalized_weights.keys())
        display_weights = {}

        for signal_id in signal_ids[:-1]:
            display_weights[signal_id] = round_half_up(normalized_weights[signal_id], decimals)

        final_signal_id = signal_ids[-1]
        display_weights[final_signal_id] = round_half_up(
            1.0 - sum(display_weights.values()),
            decimals,
        )

        return display_weights

    def aggregate(self, signals: dict[str, float], ages: dict[str, float]) -> dict[str, object]:
        """
        Run the full signal aggregation pipeline.

        :param signals: Dict of raw signal values in range [-1, 1].
        :param ages: Dict of signal ages in the same units as half-lives.
        """
        if signals.keys() != ages.keys():
            raise ValueError("Signals and ages must contain the same signal names.")

        # 1. Calculate raw time-decay weights.
        raw_weights = self._calculate_raw_weights(ages)

        # 2. Confidence / freshness score C_t.
        confidence = sum(raw_weights.values())

        if confidence == 0:
            raise ValueError("Confidence is zero; cannot normalize weights.")

        # 3. Normalize weights so they sum to 1.
        normalized_weights = {
            signal_id: weight / confidence
            for signal_id, weight in raw_weights.items()
        }
        display_normalized_weights = self._calculate_display_normalized_weights(normalized_weights)

        # 4. Normalized forecast direction F_t.
        forecast = sum(
            normalized_weights[signal_id] * signals[signal_id]
            for signal_id in signals.keys()
        )

        # 5. Optional EWMA smoothing of the combined forecast.
        smooth_forecast = (
            self.alpha * forecast
            + (1.0 - self.alpha) * self.prev_smooth_forecast
        )
        self.prev_smooth_forecast = smooth_forecast

        # 6. Threshold decision: go long, go short, or stay flat.
        if smooth_forecast > self.threshold:
            decision = "LONG"
        elif smooth_forecast < -self.threshold:
            decision = "SHORT"
        else:
            decision = "FLAT"

        # 7. Position sizing using confidence.
        position_size_multiplier = self._confidence_function_linear_with_cap(confidence)
        final_position = (
            smooth_forecast * position_size_multiplier
            if decision != "FLAT"
            else 0.0
        )

        breakdown = []

        for signal_id in signals.keys():
            breakdown.append(
                {
                    "Signal": signal_id,
                    "Value": signals[signal_id],
                    "Age": ages[signal_id],
                    "Half-Life": self.half_lives[signal_id],
                    "Raw Weight": round_half_up(raw_weights[signal_id], 3),
                    "Norm Weight": display_normalized_weights[signal_id],
                    "Contribution": round_half_up(
                        display_normalized_weights[signal_id] * signals[signal_id],
                        3,
                    ),
                }
            )

        return {
            "breakdown": pd.DataFrame(breakdown),
            "metrics": {
                "Confidence (C_t)": round_half_up(confidence, 3),
                "Sum of Normalized Weights": round_half_up(sum(display_normalized_weights.values()), 3),
                "Normalized Forecast (F_t)": round_half_up(forecast, 3),
                "Smoothed Forecast": round_half_up(smooth_forecast, 3),
                "Decision": decision,
                "Confidence Multiplier f(C)": round_half_up(position_size_multiplier, 3),
                "Final Position Size (P_t)": round_half_up(final_position, 3),
            },
        }


if __name__ == "__main__":
    # Define half-lives in minutes.
    half_lives_config = {
        "Fast": 2,  # 2 minutes
        "Medium": 60 * 4,  # 4 hours
        "Slow": 14400 * 10,  # 10 days
    }

    # Example input signals and ages.
    current_signals = {
        "Fast": 0.80,
        "Medium": 0.50,
        "Slow": -0.30,
    }
    current_ages = {
        "Fast": 10,  # 10 minutes
        "Medium": 60,  # 1 hour
        "Slow": 14400 * 2,  # 2 days
    }

    aggregator = MultiHorizonSignalAggregator(
        half_lives=half_lives_config,
        threshold=0.05,
        alpha=1.0,  # No smoothing, so the run matches the infographic's numerical example.
    )
    output = aggregator.aggregate(
        signals=current_signals,
        ages=current_ages,
    )

    print("--- SIGNAL BREAKDOWN TABLE ---")
    print(
        output["breakdown"].to_string(
            index=False,
            formatters={
                "Value": "{:.2f}".format,
                "Raw Weight": "{:.3f}".format,
                "Norm Weight": "{:.3f}".format,
                "Contribution": "{:.3f}".format,
            },
        )
    )

    print()
    print("--- EXECUTIVE METRICS ---")
    for metric, value in output["metrics"].items():
        if isinstance(value, float):
            print(f"{metric}: {value:.3f}")
        else:
            print(f"{metric}: {value}")
