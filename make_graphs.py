import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"
csv_path = RESULTS / "repeated_runs.csv"

df = pd.read_csv(csv_path)

summary = df.groupby("Scenario").agg(
    Baseline_F1_mean=("Baseline_F1", "mean"),
    Baseline_F1_sd=("Baseline_F1", "std"),
    Proposed_F1_mean=("Proposed_F1", "mean"),
    Proposed_F1_sd=("Proposed_F1", "std"),
    Baseline_FP_mean=("Baseline_FP", "mean"),
    Proposed_FP_mean=("Proposed_FP", "mean"),
).reindex(["S1", "S2", "S3"])

# 1. F1 comparison with standard-deviation error bars
x = range(len(summary))
width = 0.35

plt.figure(figsize=(8, 5))
plt.bar([i - width/2 for i in x], summary["Baseline_F1_mean"],
        width, yerr=summary["Baseline_F1_sd"], capsize=4, label="Baseline")
plt.bar([i + width/2 for i in x], summary["Proposed_F1_mean"],
        width, yerr=summary["Proposed_F1_sd"], capsize=4, label="Proposed")
plt.xticks(list(x), ["S1 Low", "S2 Medium", "S3 High"])
plt.ylabel("F1 Score")
plt.xlabel("Scenario")
plt.ylim(0, 1.1)
plt.title("Baseline vs Proposed F1 Score")
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS / "f1_comparison.png", dpi=300)
plt.close()

# 2. False-positive comparison
plt.figure(figsize=(8, 5))
plt.bar([i - width/2 for i in x], summary["Baseline_FP_mean"],
        width, label="Baseline")
plt.bar([i + width/2 for i in x], summary["Proposed_FP_mean"],
        width, label="Proposed")
plt.xticks(list(x), ["S1 Low", "S2 Medium", "S3 High"])
plt.ylabel("Average False Positives")
plt.xlabel("Scenario")
plt.title("False Positive Comparison")
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS / "false_positive_comparison.png", dpi=300)
plt.close()

# 3. F1 across all repeated runs
plt.figure(figsize=(10, 5))
for scenario in ["S1", "S2", "S3"]:
    part = df[df["Scenario"] == scenario]
    plt.plot(part["Run"], part["Baseline_F1"], marker="o",
             label=f"{scenario} Baseline")
    plt.plot(part["Run"], part["Proposed_F1"], marker="o",
             linestyle="--", label=f"{scenario} Proposed")
plt.xlabel("Run")
plt.ylabel("F1 Score")
plt.title("F1 Score Across Repeated Runs")
plt.ylim(0, 1.05)
plt.legend()
plt.tight_layout()
plt.savefig(RESULTS / "repeated_runs_f1.png", dpi=300)
plt.close()

# Save a clean summary table
summary.round(3).to_csv(RESULTS / "summary_results.csv")

print("Graphs generated successfully:")
print(RESULTS / "f1_comparison.png")
print(RESULTS / "false_positive_comparison.png")
print(RESULTS / "repeated_runs_f1.png")
print(RESULTS / "summary_results.csv")
