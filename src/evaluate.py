import numpy as np
import pandas as pd
from .config import WARMUP_WINDOWS, Z_THRESHOLD, ANOMALY_THRESHOLD
from .detectors import BaselineDetector, AdaptiveDetector
from .traffic import generate_traffic, add_live_like_noise

ALL_SCENARIOS = ("S1", "S2", "S3", "S4", "S5")


def metrics(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0
    return {"TP": tp, "TN": tn, "FP": fp, "FN": fn,
            "Precision": precision, "Recall": recall, "F1": f1}


def run_once(scenario, seed=42, z_threshold=Z_THRESHOLD,
             anomaly_threshold=ANOMALY_THRESHOLD):
    df = add_live_like_noise(generate_traffic(scenario, seed=seed), seed=seed + 100)

    b = BaselineDetector()
    a = AdaptiveDetector(z_threshold=z_threshold,
                         anomaly_threshold=anomaly_threshold)

    base_pred, prop_pred, scores = [], [], []
    base_reason, prop_reason = [], []

    for _, row in df.iterrows():
        x, r = b.detect(row)
        base_pred.append(int(x)); base_reason.append(r)

        x, s, r = a.detect(row)
        prop_pred.append(int(x)); scores.append(s); prop_reason.append(r)

    df["baseline_alert"] = base_pred
    df["proposed_alert"] = prop_pred
    df["adaptive_score"] = scores
    df["baseline_reason"] = base_reason
    df["proposed_reason"] = prop_reason
    return df


def run_repeated(scenarios=ALL_SCENARIOS, runs=10,
                 z_threshold=Z_THRESHOLD, anomaly_threshold=ANOMALY_THRESHOLD):
    rows = []
    for scenario in scenarios:
        for run in range(runs):
            df = run_once(scenario, seed=42 + run,
                          z_threshold=z_threshold,
                          anomaly_threshold=anomaly_threshold)
            # Score only after the warm-up so both detectors are compared
            # on the same windows.
            scored = df.iloc[WARMUP_WINDOWS:]
            bm = metrics(scored["label"], scored["baseline_alert"])
            pm = metrics(scored["label"], scored["proposed_alert"])
            rows.append({
                "Scenario": scenario, "Run": run + 1,
                "Baseline_F1": bm["F1"], "Proposed_F1": pm["F1"],
                "Baseline_Precision": bm["Precision"],
                "Proposed_Precision": pm["Precision"],
                "Baseline_Recall": bm["Recall"],
                "Proposed_Recall": pm["Recall"],
                "Baseline_FP": bm["FP"], "Proposed_FP": pm["FP"]
            })
    return pd.DataFrame(rows)
