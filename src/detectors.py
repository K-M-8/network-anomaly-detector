import numpy as np
from .config import (
    BASELINE_RATE, BASELINE_UNIQUE_DST, BASELINE_FAILED_CONN,
    EWMA_ALPHA, Z_THRESHOLD, ANOMALY_THRESHOLD, WARMUP_WINDOWS, MIN_SPREAD
)

# Importance of each feature when several features deviate together.
WEIGHTS = np.array([0.50, 0.30, 0.20])


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
    """Proposed detector: warm-up + EWMA baseline + z-score scoring.

    Score = max(strongest single-feature signal, weighted combined signal),
    so one strong feature can raise an alert on its own. The weights sum to 1,
    so the combined signal never exceeds the strongest one (weights inactive).

    The current window is scored before updating the baseline. Anomalous
    windows are not used to update the baseline, reducing alert masking.

    Known limitations:
    - The warm-up period is assumed to contain only normal traffic.
    - After a sudden permanent traffic shift the detector keeps alerting,
      because alert windows are never used to update the baseline.
    """
    def __init__(self, alpha=EWMA_ALPHA, z_threshold=Z_THRESHOLD,
                 anomaly_threshold=ANOMALY_THRESHOLD, warmup=WARMUP_WINDOWS):
        self.alpha = alpha
        self.z_threshold = z_threshold
        self.anomaly_threshold = anomaly_threshold
        self.warmup = warmup
        self._warmup_buffer = []   # only used during warm-up, then freed
        self.baseline = None
        self.var = None

    def _initialize(self):
        x = np.array(self._warmup_buffer, dtype=float)
        self.baseline = x.mean(axis=0)
        self.var = x.var(axis=0)
        self._warmup_buffer = []   # free memory

    def _spread(self):
        return np.maximum(np.sqrt(self.var), MIN_SPREAD)

    def detect(self, row):
        values = np.array([
            row["packet_rate"],
            row["unique_dst"],
            row["failed_conn"]
        ], dtype=float)

        # ---- warm-up: collect windows, never alert ----
        if self.baseline is None:
            self._warmup_buffer.append(values)
            if len(self._warmup_buffer) < self.warmup:
                return False, 0.0, "learning normal baseline"
            self._initialize()
            return False, 0.0, "baseline initialized"

        # ---- scoring ----
        z = np.abs((values - self.baseline) / self._spread())
        s = np.minimum(z / self.z_threshold, 2.0) / 2.0   # each in [0, 1]
        score = float(max(s.max(), (WEIGHTS * s).sum()))

        reasons = []
        if z[0] > self.z_threshold:
            reasons.append("packet-rate anomaly")
        if z[1] > self.z_threshold:
            reasons.append("destination anomaly")
        if z[2] > self.z_threshold:
            reasons.append("connection anomaly")

        alert = score >= self.anomaly_threshold

        # ---- EWMA adaptation only on normal windows ----
        if not alert:
            diff = values - self.baseline
            self.baseline = self.baseline + self.alpha * diff
            self.var = (1 - self.alpha) * (self.var + self.alpha * diff ** 2)

        return alert, score, "; ".join(reasons) if reasons else "normal"
