from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.append(str(BASE))

from src.evaluate import run_repeated

RESULTS = BASE / "results"
RESULTS.mkdir(exist_ok=True)

df = run_repeated(runs=20)
df.to_csv(RESULTS / "repeated_runs.csv", index=False)

summary = df.groupby("Scenario").agg(
    Baseline_F1_mean=("Baseline_F1", "mean"),
    Baseline_F1_sd=("Baseline_F1", "std"),
    Proposed_F1_mean=("Proposed_F1", "mean"),
    Proposed_F1_sd=("Proposed_F1", "std"),
    Baseline_FP_mean=("Baseline_FP", "mean"),
    Proposed_FP_mean=("Proposed_FP", "mean"),
)
print(summary.round(3).to_string())
print(f"\nSaved: {RESULTS / 'repeated_runs.csv'}")
