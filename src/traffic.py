import numpy as np
import pandas as pd
from .config import RANDOM_SEED

def generate_traffic(scenario="S1", n=300, seed=RANDOM_SEED):
    """Generate reproducible normal/anomalous network-window data.
    This is safe synthetic data for evaluation without generating real attacks.
    """
    rng = np.random.default_rng(seed)
    t = np.arange(n)

    # Normal background traffic.
    packet_rate = rng.normal(35, 6, n).clip(5)
    unique_dst = rng.normal(8, 2, n).clip(1)
    failed_conn = rng.normal(3, 1.2, n).clip(0)

    labels = np.zeros(n, dtype=int)

    if scenario == "S1":
        # Low load: a short mild spike.
        idx = slice(100, 120)
        packet_rate[idx] += 60
        unique_dst[idx] += 8
        labels[idx] = 1

    elif scenario == "S2":
        # Medium load: moderate sustained anomaly.
        packet_rate += 15
        unique_dst += 4
        idx = slice(120, 155)
        packet_rate[idx] += 55
        unique_dst[idx] += 10
        failed_conn[idx] += 8
        labels[idx] = 1

    elif scenario == "S3":
        # High load: normal traffic is already high; anomaly is a burst.
        packet_rate += 35
        unique_dst += 8
        failed_conn += 3
        idx = slice(130, 180)
        packet_rate[idx] += 65
        unique_dst[idx] += 15
        failed_conn[idx] += 10
        labels[idx] = 1

    else:
        raise ValueError("Scenario must be S1, S2 or S3")

    return pd.DataFrame({
        "time": t,
        "packet_rate": packet_rate,
        "unique_dst": unique_dst,
        "failed_conn": failed_conn,
        "label": labels
    })

def add_live_like_noise(df, seed=123):
    rng = np.random.default_rng(seed)
    out = df.copy()
    out["packet_rate"] += rng.normal(0, 2, len(out))
    out["unique_dst"] += rng.normal(0, .5, len(out))
    out["failed_conn"] += rng.normal(0, .3, len(out))
    return out.clip(lower=0)
