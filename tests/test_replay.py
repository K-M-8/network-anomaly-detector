"""Run with:  python tests/test_replay.py"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from replay_pcap import build_windows, run_detectors, add_labels, demo_packets
from src.evaluate import metrics
from src.config import WARMUP_WINDOWS


def test_windows_group_and_count_features():
    packets = [
        (0.1, "10.0.0.1", False),
        (0.5, "10.0.0.2", True),
        (0.9, "10.0.0.2", True),
        (2.2, "10.0.0.3", False),     # window 3; window 2 is empty
    ]
    df = build_windows(packets)
    assert list(df["window"]) == [1, 2, 3]
    assert list(df["packet_rate"]) == [3.0, 0.0, 1.0]
    assert list(df["unique_dst"]) == [2, 0, 1]
    assert list(df["failed_conn"]) == [2, 0, 0]


def test_non_ip_packets_count_toward_rate_only():
    df = build_windows([(0.0, None, False), (0.2, None, False)])
    assert df.loc[0, "packet_rate"] == 2.0
    assert df.loc[0, "unique_dst"] == 0


def test_empty_capture_gives_empty_frame():
    assert len(build_windows([])) == 0


def test_demo_attack_is_detected_after_warmup():
    df = add_labels(run_detectors(build_windows(demo_packets())), [100, 125])
    scored = df[df["window"] > WARMUP_WINDOWS]
    m = metrics(scored["label"], scored["proposed_alert"])
    assert m["Recall"] > 0.9, m


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
    print("All tests passed.")