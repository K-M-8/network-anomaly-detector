"""Run with:  python tests/test_detectors.py"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.detectors import AdaptiveDetector, BaselineDetector
from src.traffic import generate_traffic

NORMAL = {"packet_rate": 35, "unique_dst": 8, "failed_conn": 3}


def warmed_detector():
    d = AdaptiveDetector()
    for _ in range(30):
        d.detect(NORMAL)
    return d


def test_baseline_fires_on_each_feature():
    b = BaselineDetector()
    assert b.detect({"packet_rate": 500, "unique_dst": 1, "failed_conn": 0})[0]
    assert b.detect({"packet_rate": 1, "unique_dst": 500, "failed_conn": 0})[0]
    assert b.detect({"packet_rate": 1, "unique_dst": 1, "failed_conn": 500})[0]
    assert not b.detect(NORMAL)[0]


def test_adaptive_never_alerts_during_warmup():
    d = AdaptiveDetector()
    for _ in range(29):
        alert, _, _ = d.detect({"packet_rate": 9999, "unique_dst": 999, "failed_conn": 999})
        assert not alert


def test_adaptive_detects_single_feature_attacks():
    for attack in (
        {"packet_rate": 5000, "unique_dst": 8, "failed_conn": 3},
        {"packet_rate": 35, "unique_dst": 500, "failed_conn": 3},
        {"packet_rate": 35, "unique_dst": 8, "failed_conn": 5000},
    ):
        assert warmed_detector().detect(attack)[0], attack


def test_adaptive_quiet_on_normal_traffic():
    d = warmed_detector()
    assert not d.detect(NORMAL)[0]


def test_warmup_buffer_is_freed():
    d = AdaptiveDetector()
    for _ in range(500):
        d.detect(NORMAL)
    assert len(d._warmup_buffer) == 0


def test_every_scenario_contains_anomalies_at_demo_length():
    for s in ("S1", "S2", "S3", "S4", "S5"):
        assert generate_traffic(s, n=300)["label"].sum() > 0, s


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
    print("All tests passed.")
