import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import time
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

from src.traffic import generate_traffic
from src.detectors import BaselineDetector, AdaptiveDetector
from src.evaluate import run_repeated


st.set_page_config(
    page_title="Real-Time Network Attack / Anomaly Detector",
    layout="wide"
)

st.title("Real-Time Network Attack / Anomaly Detector")
st.caption(
    "Baseline: fixed thresholds | "
    "Proposed: adaptive EWMA-style learning + weighted z-score"
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    st.header("Demo Controls")

    scenario = st.selectbox(
        "Scenario",
        ["S1", "S2", "S3"]
    )

    z_threshold = st.slider(
        "Adaptive z-threshold",
        1.0,
        4.0,
        3.0,
        0.1
    )

    anomaly_threshold = st.slider(
        "Anomaly score threshold",
        0.2,
        0.9,
        0.55,
        0.05
    )

    runs = st.slider(
        "Repeated runs",
        3,
        30,
        20
    )

    st.divider()

    st.info(
        "Demo configuration\n\n"
        "Z-threshold: 3.0\n\n"
        "Anomaly threshold: 0.55\n\n"
        "Evaluation runs: 20"
    )


# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------

tab1, tab2, tab3 = st.tabs(
    ["Live Demo", "Performance Evaluation", "Method / Limitations"]
)


# =========================================================
# TAB 1 - LIVE DEMO
# =========================================================

with tab1:

    st.subheader("Live baseline vs proposed")

    st.write(
        f"Scenario: **{scenario}**  |  "
        f"Z-threshold: **{z_threshold:.2f}**  |  "
        f"Anomaly threshold: **{anomaly_threshold:.2f}**"
    )

    start = st.button(
        "▶ Start Simulation",
        type="primary"
    )

    if start:

        df = generate_traffic(scenario, n=120)

        base = BaselineDetector()

        prop = AdaptiveDetector(
            z_threshold=z_threshold,
            anomaly_threshold=anomaly_threshold
        )

        placeholder = st.empty()
        progress = st.progress(0)

        alerts = []

        for i, (_, row) in enumerate(df.iterrows(), start=1):

            # -----------------------------
            # Run baseline
            # -----------------------------

            b, br = base.detect(row)

            # -----------------------------
            # Run proposed
            # -----------------------------

            p, score, pr = prop.detect(row)

            alerts.append(
                [
                    i,
                    bool(b),
                    bool(p),
                    float(score)
                ]
            )

            live = pd.DataFrame(
                alerts,
                columns=[
                    "Window",
                    "Baseline",
                    "Proposed",
                    "Score"
                ]
            )

            # -----------------------------
            # Current traffic values
            # -----------------------------

            packet_rate = row.get(
                "packet_rate",
                0
            )

            destinations = row.get(
                "dst_diversity",
                row.get("destinations", "N/A")
            )

            syn_count = row.get(
                "syn_count",
                row.get("syn", "N/A")
            )

            # -----------------------------
            # Dashboard
            # -----------------------------

            with placeholder.container():

                st.markdown(
                    f"### Traffic Window {i}/120"
                )

                # Main status cards
                c1, c2, c3, c4 = st.columns(4)

                c1.metric(
                    "Packet Rate",
                    f"{float(packet_rate):.1f}/s"
                )

                c2.metric(
                    "Destinations",
                    str(destinations)
                )

                c3.metric(
                    "SYN Count",
                    str(syn_count)
                )

                c4.metric(
                    "Anomaly Score",
                    f"{float(score):.2f}"
                )

                st.divider()

                # Baseline vs Proposed
                b1, b2 = st.columns(2)

                with b1:
                    if b:
                        st.error("BASELINE: ALERT")
                    else:
                        st.success("BASELINE: NORMAL")

                    st.write(br)

                with b2:
                    if p:
                        st.error("PROPOSED: ALERT")
                    else:
                        st.success("PROPOSED: NORMAL")

                    st.write(pr)

                st.divider()

                # -------------------------
                # Clean graph
                # -------------------------

                fig, ax = plt.subplots(figsize=(10, 4))

                ax.plot(
                    live["Window"],
                    live["Score"],
                    label="Anomaly Score",
                    linewidth=2
                )

                ax.plot(
                    live["Window"],
                    live["Baseline"].astype(int),
                    label="Baseline",
                    linestyle="--"
                )

                ax.plot(
                    live["Window"],
                    live["Proposed"].astype(int),
                    label="Proposed",
                    linestyle="--"
                )

                ax.axhline(
                    anomaly_threshold,
                    linestyle=":",
                    label="Anomaly Threshold"
                )

                ax.set_xlabel("Traffic Window")
                ax.set_ylabel("Score / Decision")
                ax.set_ylim(-0.05, 1.10)
                ax.set_title(
                    "Live Anomaly Score and Detector Decisions"
                )
                ax.legend()
                ax.grid(alpha=0.25)

                st.pyplot(
                    fig,
                    clear_figure=True
                )

                # -------------------------
                # Latest explanation
                # -------------------------

                st.markdown("#### Latest Detection")

                e1, e2 = st.columns(2)

                with e1:
                    st.write(
                        "**Baseline explanation:**"
                    )
                    st.write(br)

                with e2:
                    st.write(
                        "**Proposed explanation:**"
                    )
                    st.write(pr)

            progress.progress(
                i / len(df)
            )

            # Small delay for live effect
            time.sleep(0.05)

        progress.empty()

        st.success(
            "Simulation completed successfully."
        )

        # Final summary
        total_baseline = sum(x[1] for x in alerts)
        total_proposed = sum(x[2] for x in alerts)

        st.markdown("### Simulation Summary")

        s1, s2, s3 = st.columns(3)

        s1.metric(
            "Baseline Alerts",
            total_baseline
        )

        s2.metric(
            "Proposed Alerts",
            total_proposed
        )

        s3.metric(
            "Total Windows",
            len(alerts)
        )


# =========================================================
# TAB 2 - PERFORMANCE EVALUATION
# =========================================================

with tab2:

    st.subheader("Repeated-run Performance Evaluation")

    st.write(
        "Each scenario is evaluated using repeated runs "
        "to compare the fixed-threshold baseline with the "
        "adaptive proposed detector."
    )

    if st.button(
        "Run Evaluation",
        type="primary"
    ):

        with st.spinner(
            f"Running {runs} repetitions per scenario..."
        ):

            raw = run_repeated(
                runs=runs
            )

        summary = raw.groupby("Scenario").agg(

            Baseline_F1_mean=(
                "Baseline_F1",
                "mean"
            ),

            Baseline_F1_sd=(
                "Baseline_F1",
                "std"
            ),

            Proposed_F1_mean=(
                "Proposed_F1",
                "mean"
            ),

            Proposed_F1_sd=(
                "Proposed_F1",
                "std"
            ),

            Baseline_FP_mean=(
                "Baseline_FP",
                "mean"
            ),

            Proposed_FP_mean=(
                "Proposed_FP",
                "mean"
            ),

        ).reset_index()

        # Round for display
        display_summary = summary.copy()

        numeric_columns = display_summary.select_dtypes(
            include="number"
        ).columns

        display_summary[numeric_columns] = (
            display_summary[numeric_columns]
            .round(3)
        )

        st.dataframe(
            display_summary,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### F1 Score Comparison")

        fig, ax = plt.subplots(
            figsize=(9, 4)
        )

        x = range(len(summary))

        ax.bar(
            [i - 0.18 for i in x],
            summary["Baseline_F1_mean"],
            width=0.36,
            label="Baseline"
        )

        ax.bar(
            [i + 0.18 for i in x],
            summary["Proposed_F1_mean"],
            width=0.36,
            label="Proposed"
        )

        ax.set_xticks(
            list(x),
            summary["Scenario"]
        )

        ax.set_ylabel("F1 Score")
        ax.set_ylim(0, 1.1)
        ax.set_title(
            "Baseline vs Proposed F1 Score"
        )

        ax.legend()
        ax.grid(
            axis="y",
            alpha=0.25
        )

        st.pyplot(
            fig,
            clear_figure=True
        )

        st.markdown("### False Positive Comparison")

        fig2, ax2 = plt.subplots(
            figsize=(9, 4)
        )

        ax2.bar(
            [i - 0.18 for i in x],
            summary["Baseline_FP_mean"],
            width=0.36,
            label="Baseline"
        )

        ax2.bar(
            [i + 0.18 for i in x],
            summary["Proposed_FP_mean"],
            width=0.36,
            label="Proposed"
        )

        ax2.set_xticks(
            list(x),
            summary["Scenario"]
        )

        ax2.set_ylabel(
            "Average False Positives"
        )

        ax2.set_title(
            "False Positive Comparison"
        )

        ax2.legend()
        ax2.grid(
            axis="y",
            alpha=0.25
        )

        st.pyplot(
            fig2,
            clear_figure=True
        )

        st.download_button(
            "Download Raw Results CSV",
            raw.to_csv(index=False),
            "results.csv",
            "text/csv"
        )


# =========================================================
# TAB 3 - METHOD / LIMITATIONS
# =========================================================

with tab3:

    st.subheader("Method")

    st.markdown("""
### Baseline

Uses fixed thresholds for:

- Packet rate
- Destination diversity
- Failed connections

It does not adapt its thresholds to changing traffic behaviour.

### Proposed

The proposed detector learns the recent traffic profile using
an EWMA-style adaptive mechanism.

It combines multiple normalized anomaly signals:

- Packet-rate anomaly
- Destination-diversity anomaly
- Connection/SYN anomaly

A weighted anomaly score is then compared with the selected
threshold.

This allows the detector to adapt when normal traffic levels
change.

### Why it is better

The main advantage is visible under **high-load traffic (S3)**,
where a fixed threshold can interpret legitimate high traffic
as an attack.

The proposed detector adapts to the changing traffic profile
and reduces false positives.
""")

    st.subheader("Limitations")

    st.markdown("""
- Synthetic evaluation is not equivalent to production traffic.
- Real packet capture requires appropriate OS capture support.
- Network monitoring must only be performed on authorized networks.
- Encrypted payload contents cannot be inspected using these features.
- Thresholds still require tuning for a real deployment.
- The current implementation focuses on traffic metadata rather
  than deep packet inspection.
""")

    st.subheader("Demo Configuration")

    st.code("""
Scenario: S1 / S2 / S3
Adaptive z-threshold: 3.0
Anomaly score threshold: 0.55
Repeated evaluation runs: 20
Live simulation windows: 120
    """)