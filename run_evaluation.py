from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from src.evaluate import run_repeated

Path("results").mkdir(exist_ok=True)
df = run_repeated(runs=20)
df.to_csv("results/repeated_runs.csv", index=False)

summary = df.groupby("Scenario").agg(
    Baseline_F1_mean=("Baseline_F1","mean"),
    Baseline_F1_sd=("Baseline_F1","std"),
    Proposed_F1_mean=("Proposed_F1","mean"),
    Proposed_F1_sd=("Proposed_F1","std"),
    Baseline_FP_mean=("Baseline_FP","mean"),
    Proposed_FP_mean=("Proposed_FP","mean"),
)
print(summary.round(3))
print("\nSaved: results/repeated_runs.csv")
