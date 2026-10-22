import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent
RESULTS = BASE / "results"
FIGURES = BASE / "reports" / "figures"      # figures used by the README
FIGURES.mkdir(parents=True, exist_ok=True)
csv_path = RESULTS / "repeated_runs.csv"

SCENARIOS = ["S1", "S2", "S3", "S4", "S5"]
LABELS = ["S1 Low", "S2 Medium", "S3 High", "S4 Drift", "S5 Single-feature"]

df = pd.read_csv(csv_path)

summary = df.groupby("Scenario").agg(
    Baseline_F1_mean=("Baseline_F1", "mean"),
    Baseline_F1_sd=("Baseline_F1", "std"),
    Proposed_F1_mean=("Proposed_F1", "mean"),
    Proposed_F1_sd=("Proposed_F1", "std"),
    Baseline_FP_mean=("Baseline_FP", "mean"),
    Proposed_FP_mean=("Proposed_FP", "mean"),
).reindex(SCENARIOS)

# 1. F1 comparison with standard-deviation error bars
x = range(len(summary))
width = 0.35

plt.figure(figsize=(10, 5))
plt.bar([i - width/2 for i in x], summary["Baseline_F1_mean"],
        width, yerr=summary["Baseline_F1_sd"], capsize=4, label="Baseline")
plt.bar([i + width/2 for i in x], summary["Proposed_F1_mean"],
        width, yerr=summary["Proposed_F1_sd"], capsize=4, label="Proposed")
plt.xticks(list(x), LABELS)
plt.ylabel("F1 Score")
plt.xlabel("Scenario")
plt.ylim(0, 1.2)
plt.title("Baseline vs Proposed F1 Score")
plt.legend(loc="upper center", ncol=2)
plt.tight_layout()
plt.savefig(FIGURES / "f1_comparison.png", dpi=300)
plt.close()

# 2. False-positive comparison
plt.figure(figsize=(10, 5))
plt.bar([i - width/2 for i in x], summary["Baseline_FP_mean"],
        width, label="Baseline")
plt.bar([i + width/2 for i in x], summary["Proposed_FP_mean"],
        width, label="Proposed")
plt.xticks(list(x), LABELS)
plt.ylabel("Average False Positives")
plt.xlabel("Scenario")
plt.title("False Positive Comparison")
plt.legend()
plt.tight_layout()
plt.savefig(FIGURES / "false_positive_comparison.png", dpi=300)
plt.close()

# 3. F1 across all repeated runs (one panel per scenario)
runs = sorted(df["Run"].unique())
ticks = [r for r in runs if r == 1 or r % 5 == 0]

fig, axes = plt.subplots(2, 3, figsize=(13, 7), sharex=True, sharey=True)
axes = axes.flatten()

for ax, scenario, label in zip(axes, SCENARIOS, LABELS):
    part = df[df["Scenario"] == scenario]
    ax.plot(part["Run"], part["Baseline_F1"], marker="o", markersize=4,
            color="tab:blue", label="Baseline")
    ax.plot(part["Run"], part["Proposed_F1"], marker="o", markersize=4,
            linestyle="--", color="tab:orange", label="Proposed")
    ax.set_title(label)
    ax.set_ylim(0, 1.05)
    ax.set_xticks(ticks)
    ax.grid(alpha=0.25)

# Sixth panel holds the legend
axes[5].axis("off")
handles, labels = axes[0].get_legend_handles_labels()
axes[5].legend(handles, labels, loc="center", fontsize=12)

for ax in axes[2:5]:
    ax.set_xlabel("Run")
    ax.tick_params(labelbottom=True)
axes[0].set_ylabel("F1 Score")
axes[3].set_ylabel("F1 Score")

fig.suptitle("F1 Score Across Repeated Runs")
fig.tight_layout()
fig.savefig(FIGURES / "repeated_runs_f1.png", dpi=300)
plt.close(fig)

# Save a clean summary table
summary.round(3).to_csv(RESULTS / "summary_results.csv")

print("Graphs generated successfully:")
print(FIGURES / "f1_comparison.png")
print(FIGURES / "false_positive_comparison.png")
print(FIGURES / "repeated_runs_f1.png")
print(RESULTS / "summary_results.csv")