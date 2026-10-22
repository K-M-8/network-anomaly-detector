"""Replay a recorded packet capture (.pcap / .pcapng) through both detectors.

Uses the same three features as live_capture.py, computed per time window:
    packet_rate  - packets per second
    unique_dst   - number of distinct destination IP addresses
    failed_conn  - number of TCP packets with the SYN flag set (a
                   connection-attempt proxy, not a count of failed connections)

Examples
--------
    python replay_pcap.py --demo
    python replay_pcap.py capture.pcapng
    python replay_pcap.py capture.pcapng --attack 120 150

--attack START END marks the windows (1-based, inclusive) in which you
deliberately ran a test, for example a port scan on a network you own or are
authorised to test. With it, precision / recall / F1 are reported.
Without it, there are no labels, so the script reports alert counts only.

Only use captures from networks you are authorised to monitor.
"""

import argparse
import random
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
sys.path.append(str(BASE))

from src.config import WARMUP_WINDOWS, Z_THRESHOLD, ANOMALY_THRESHOLD
from src.detectors import BaselineDetector, AdaptiveDetector
from src.evaluate import metrics

COLUMNS = ["window", "packet_rate", "unique_dst", "failed_conn"]


# ---------------------------------------------------------
# 1. Reading packets
# ---------------------------------------------------------

def packets_from_pcap(path):
    """Yield (timestamp, destination_ip_or_None, is_syn) for each packet."""
    from scapy.all import PcapReader, IP, TCP   # imported here so tests need no Scapy

    with PcapReader(str(path)) as reader:
        for p in reader:
            dst = p[IP].dst if IP in p else None
            syn = bool(TCP in p and int(p[TCP].flags) & 0x02)
            yield float(p.time), dst, syn


def demo_packets(seconds=150, attack=(100, 125), seed=42):
    """Synthetic packet stream for testing the script without a capture file."""
    rng = random.Random(seed)
    for sec in range(seconds):
        under_attack = attack[0] <= sec + 1 <= attack[1]
        n = rng.randint(250, 320) if under_attack else rng.randint(25, 45)
        for k in range(n):
            t = sec + k / n
            if under_attack:
                dst = f"10.0.{rng.randint(0, 3)}.{rng.randint(1, 254)}"
                syn = rng.random() < 0.35
            else:
                dst = f"192.168.1.{rng.randint(1, 8)}"
                syn = rng.random() < 0.05
            yield t, dst, syn


# ---------------------------------------------------------
# 2. Turning packets into per-window features
# ---------------------------------------------------------

def build_windows(packets, window=1.0):
    """Group (timestamp, dst, is_syn) tuples into fixed windows.

    Seconds with no packets become rows of zeros, so the timeline has no gaps.
    """
    counts = {}
    t0 = None

    for t, dst, syn in packets:
        if t0 is None:
            t0 = t
        idx = max(int((t - t0) // window), 0)
        w = counts.setdefault(idx, {"packets": 0, "dst": set(), "syn": 0})
        w["packets"] += 1
        if dst is not None:
            w["dst"].add(dst)
        if syn:
            w["syn"] += 1

    if not counts:
        return pd.DataFrame(columns=COLUMNS)

    rows = []
    for idx in range(max(counts) + 1):
        w = counts.get(idx)
        rows.append({
            "window": idx + 1,
            "packet_rate": w["packets"] / window if w else 0.0,
            "unique_dst": len(w["dst"]) if w else 0,
            "failed_conn": w["syn"] if w else 0,
        })
    return pd.DataFrame(rows, columns=COLUMNS)


# ---------------------------------------------------------
# 3. Running the detectors
# ---------------------------------------------------------

def run_detectors(df, z_threshold=Z_THRESHOLD, anomaly_threshold=ANOMALY_THRESHOLD):
    base = BaselineDetector()
    prop = AdaptiveDetector(z_threshold=z_threshold,
                            anomaly_threshold=anomaly_threshold)

    out = df.copy()
    b_alert, p_alert, scores = [], [], []

    for _, row in out.iterrows():
        b, _ = base.detect(row)
        p, score, _ = prop.detect(row)
        b_alert.append(int(b))
        p_alert.append(int(p))
        scores.append(score)

    out["baseline_alert"] = b_alert
    out["proposed_alert"] = p_alert
    out["adaptive_score"] = scores
    return out


def add_labels(df, attack):
    df = df.copy()
    df["label"] = 0
    if attack:
        start, end = attack
        df.loc[(df["window"] >= start) & (df["window"] <= end), "label"] = 1
    return df


# ---------------------------------------------------------
# 4. Report and plot
# ---------------------------------------------------------

def make_plot(df, anomaly_threshold, attack, out_path, title):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6), sharex=True)

    ax1.plot(df["window"], df["packet_rate"], color="tab:blue", label="Packets / s")
    ax1.set_ylabel("Packets / s")
    ax1.set_title(title)
    ax1.grid(alpha=0.25)

    ax2.plot(df["window"], df["adaptive_score"], color="tab:blue",
             label="Adaptive score")
    ax2.axhline(anomaly_threshold, color="tab:purple", linestyle=":",
                label=f"Threshold ({anomaly_threshold:.2f})")
    ax2.plot(df["window"], df["baseline_alert"] - 0.03, color="tab:orange",
             linewidth=2, label="Baseline alert")
    ax2.plot(df["window"], df["proposed_alert"], color="tab:green",
             linestyle="--", linewidth=2, label="Proposed alert")
    ax2.set_ylim(-0.1, 1.4)
    ax2.set_xlabel("Window (seconds)")
    ax2.set_ylabel("Score / decision")
    ax2.legend(loc="upper left", ncol=2, fontsize=8)
    ax2.grid(alpha=0.25)

    if attack:
        for ax in (ax1, ax2):
            ax.axvspan(attack[0], attack[1], color="red", alpha=0.08)

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def print_report(df, attack):
    scored = df[df["window"] > WARMUP_WINDOWS]

    print(f"\nWindows analysed : {len(df)}  (first {WARMUP_WINDOWS} are warm-up)")
    print("Feature summary:")
    print(df[["packet_rate", "unique_dst", "failed_conn"]]
          .agg(["mean", "max"]).round(1).to_string())

    print("\nAlerts after warm-up:")
    print(f"  Baseline : {int(scored['baseline_alert'].sum())}")
    print(f"  Proposed : {int(scored['proposed_alert'].sum())}")

    if attack:
        print(f"\nLabelled test windows: {attack[0]}-{attack[1]}")
        for name, col in (("Baseline", "baseline_alert"), ("Proposed", "proposed_alert")):
            m = metrics(scored["label"], scored[col])
            print(f"  {name}: TP={m['TP']} FP={m['FP']} FN={m['FN']}  "
                  f"precision={m['Precision']:.2f} recall={m['Recall']:.2f} "
                  f"F1={m['F1']:.2f}")
    else:
        print("\nNo --attack range given, so there are no labels.")
        print("If this capture is known to be clean, every alert above is a "
              "false alarm.")


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pcap", nargs="?", help="path to a .pcap or .pcapng file")
    parser.add_argument("--demo", action="store_true",
                        help="use a built-in synthetic packet stream")
    parser.add_argument("--window", type=float, default=1.0,
                        help="window length in seconds (default 1.0)")
    parser.add_argument("--attack", nargs=2, type=int, metavar=("START", "END"),
                        help="windows (1-based, inclusive) where a test was run")
    parser.add_argument("--z", type=float, default=Z_THRESHOLD)
    parser.add_argument("--threshold", type=float, default=ANOMALY_THRESHOLD)
    args = parser.parse_args()

    if args.demo:
        packets = demo_packets()
        name = "demo"
        if args.attack is None:
            args.attack = [100, 125]
    elif args.pcap:
        path = Path(args.pcap)
        if not path.exists():
            sys.exit(f"File not found: {path}")
        try:
            packets = packets_from_pcap(path)
        except ImportError:
            sys.exit("Scapy is required to read capture files: pip install scapy")
        name = path.stem
    else:
        parser.error("give a capture file, or use --demo")

    df = build_windows(packets, args.window)
    if len(df) <= WARMUP_WINDOWS:
        sys.exit(f"Only {len(df)} windows found; need more than {WARMUP_WINDOWS} "
                 "(record a longer capture).")

    df = add_labels(run_detectors(df, args.z, args.threshold), args.attack)
    print_report(df, args.attack)

    out_dir = BASE / "results"
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / f"replay_{name}.csv"
    png_path = out_dir / f"replay_{name}.png"
    df.to_csv(csv_path, index=False)
    make_plot(df, args.threshold, args.attack, png_path,
              f"Replay of {name}: baseline vs proposed")
    print(f"\nSaved: {csv_path}\nSaved: {png_path}")


if __name__ == "__main__":
    main()