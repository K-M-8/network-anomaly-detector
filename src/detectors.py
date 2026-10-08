import numpy as np
from .config import (
    BASELINE_RATE, BASELINE_UNIQUE_DST, BASELINE_FAILED_CONN,
    EWMA_ALPHA, Z_THRESHOLD, ANOMALY_THRESHOLD
)

class BaselineDetector:
    """Fixed-threshold detector."""

    def detect(self, row):
        reasons = []
        if row["packet_rate"] > BASELINE_RATE:
            reasons.append("high packet rate")
        if row["unique_dst"] > BASELINE_UNIQUE_DST:
            reasons.append("high destination diversity")
        if row["failed_conn"] > BASELINE_FAILED_CONN:
            reasons.append("many failed connections")
        return bool(reasons), "; ".join(reasons) if reasons else "normal"


class AdaptiveDetector:
    """Proposed detector: warm-up + EWMA baseline + weighted z-score.

    The current window is scored before updating the baseline. Anomalous
    windows are not used to update the baseline, reducing alert masking.
    """

    def __init__(self, alpha=EWMA_ALPHA, z_threshold=Z_THRESHOLD,
                 anomaly_threshold=ANOMALY_THRESHOLD, warmup=30):
        self.alpha = alpha
        self.z_threshold = z_threshold
        self.anomaly_threshold = anomaly_threshold
        self.warmup = warmup
        self.history = []
        self.baseline = None
        self.spread = None

    def _initialize(self):
        x = np.array(self.history, dtype=float)
        self.baseline = x.mean(axis=0)
        self.spread = x.std(axis=0) + 1.0

    def detect(self, row):
        values = np.array([
            row["packet_rate"],
            row["unique_dst"],
            row["failed_conn"]
        ], dtype=float)

        self.history.append(values)

        if self.baseline is None:
            if len(self.history) < self.warmup:
                return False, 0.0, "learning normal baseline"
            self._initialize()
            return False, 0.0, "baseline initialized"

        z = np.abs((values - self.baseline) / self.spread)

        score = (
            0.50 * min(z[0] / self.z_threshold, 2.0) +
            0.30 * min(z[1] / self.z_threshold, 2.0) +
            0.20 * min(z[2] / self.z_threshold, 2.0)
        ) / 2.0

        reasons = []
        if z[0] > self.z_threshold:
            reasons.append("packet-rate anomaly")
        if z[1] > self.z_threshold:
            reasons.append("destination anomaly")
        if z[2] > self.z_threshold:
            reasons.append("connection anomaly")

        alert = score >= self.anomaly_threshold

        # EWMA adaptation happens only for normal windows.
        if not alert:
            old_baseline = self.baseline.copy()
            self.baseline = (
                (1 - self.alpha) * self.baseline + self.alpha * values
            )
            self.spread = (
                (1 - self.alpha) * self.spread
                + self.alpha * np.abs(values - old_baseline)
            )
            self.spread = np.maximum(self.spread, 1.0)

        return alert, float(score), "; ".join(reasons) if reasons else "normal"
