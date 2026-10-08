"""Optional live packet-metadata monitor.

Use only on a network/interface you are authorized to monitor.
It does not inspect payloads. The third feature is TCP SYN count,
used as a lightweight connection-attempt proxy.
"""

import time
from collections import Counter
from scapy.all import sniff, IP, TCP

from src.detectors import BaselineDetector, AdaptiveDetector

WINDOW = 1.0

def collect_window():
    packets = sniff(timeout=WINDOW, store=True)
    packet_rate = len(packets) / WINDOW
    destinations = set()
    syn_count = 0

    for p in packets:
        if IP in p:
            destinations.add(p[IP].dst)
        if TCP in p and p[TCP].flags & 0x02:  # SYN
            syn_count += 1

    return {
        "packet_rate": packet_rate,
        "unique_dst": len(destinations),
        "failed_conn": syn_count
    }

def main():
    print("Live metadata monitor. Press Ctrl+C to stop.")
    print("Monitor only interfaces/networks you are authorized to inspect.\n")

    baseline = BaselineDetector()
    proposed = AdaptiveDetector()

    try:
        while True:
            row = collect_window()
            b_alert, b_reason = baseline.detect(row)
            p_alert, p_score, p_reason = proposed.detect(row)

            print(
                f"rate={row['packet_rate']:6.1f}/s  "
                f"dst={row['unique_dst']:3d}  "
                f"syn={row['failed_conn']:3d} | "
                f"baseline={'ALERT' if b_alert else 'OK':5s} | "
                f"proposed={'ALERT' if p_alert else 'OK':5s} "
                f"score={p_score:.2f}"
            )
            if b_alert:
                print("  baseline:", b_reason)
            if p_alert:
                print("  proposed:", p_reason)

    except KeyboardInterrupt:
        print("\nStopped.")

if __name__ == "__main__":
    main()
