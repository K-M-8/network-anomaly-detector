# Real-Time Network Attack / Anomaly Detector

A network anomaly detection system that compares a traditional fixed-threshold detector with a proposed adaptive anomaly detector.

## Overview

The project detects suspicious network behaviour using traffic-level metadata and compares:

- **Baseline:** Fixed-threshold detection.
- **Proposed:** Adaptive EWMA-style learning with weighted z-score anomaly detection.

The system includes a Streamlit dashboard for traffic simulation, repeated-run evaluation, visualization, and performance comparison.

## Key Features

- Real-time traffic simulation
- Baseline vs. proposed detector comparison
- Adaptive anomaly detection
- EWMA-based traffic profiling
- Weighted anomaly scoring
- Runtime threshold controls
- F1-score, precision, and recall evaluation
- False-positive comparison
- Repeated-run statistical evaluation
- Interactive Streamlit dashboard with adjustable playback speed
- Unit tests for both detectors
- Optional real packet metadata capture

## Detection Method

### Baseline Detector

The baseline uses fixed thresholds for:
- Packet rate
- Destination diversity
- Failed connection behaviour

An alert is generated when a traffic feature exceeds its configured threshold.

### Proposed Adaptive Detector

The proposed method:

1. Learns the normal traffic profile during a 30-window warm-up period.
2. Updates the profile using EWMA-style adaptation (mean and variance).
3. Calculates normalized z-score deviations for packet rate, destination diversity, and connection attempts.
4. Combines them into an anomaly score: the larger of the strongest single-feature signal and a weighted combination of all three, so one strong feature can raise an alert on its own.
5. Generates an alert when the anomaly score exceeds the configured threshold (default 0.60).

Windows flagged as anomalous are not used to update the profile, which reduces the chance that an attack is absorbed into "normal".

## Experimental Scenarios

| Scenario | Description |
|---|---|
| S1 | Low-load traffic with a multi-feature attack |
| S2 | Medium-load traffic with a multi-feature attack |
| S3 | High-load traffic (constantly elevated normal level) with a multi-feature attack |
| S4 | Gradual legitimate load growth, then a multi-feature attack |
| S5 | Single-feature attacks: a quiet packet-rate rise below the fixed limit, and a connection-attempt burst |

The evaluation uses synthetic traffic for safe, reproducible experiments without generating real attacks.

## Results

The system was evaluated using 20 repeated runs per scenario. The first 30 warm-up windows are excluded from scoring so both detectors are compared on the same windows.

| Scenario | Baseline F1 | Proposed F1 | Baseline Avg. FP | Proposed Avg. FP |
|---|---:|---:|---:|---:|
| S1 | 0.997 | 0.957 | 0.00 | 1.85 |
| S2 | 1.000 | 0.979 | 0.00 | 1.55 |
| S3 | 0.836 | 0.985 | 19.80 | 1.55 |
| S4 | 0.784 | 0.975 | 19.40 | 1.80 |
| S5 | 0.670 | 0.848 | 0.00 | 1.55 |

### Result Visualizations

#### F1 Score Comparison

![F1 Score Comparison](reports/figures/f1_comparison.png)

#### False Positive Comparison

![False Positive Comparison](reports/figures/false_positive_comparison.png)

#### Repeated-Run F1 Scores

![Repeated-Run F1 Scores](reports/figures/repeated_runs_f1.png)

### Main Result

- **High or growing load (S3, S4):** the proposed detector raises F1 from 0.836 to 0.985 (S3) and from 0.784 to 0.975 (S4), and cuts average false positives from about 20 to under 2.
- **Single-feature attacks (S5):** recall rises from 0.50 to 0.78 and F1 from 0.670 to 0.848, because the adaptive detector notices attacks that stay below the fixed limits.
- **Low and medium load (S1, S2):** the fixed baseline is slightly better (F1 0.997 vs 0.957, and 1.000 vs 0.979), because its thresholds already suit that traffic and the adaptive detector produces about 1.5 to 2 false alarms per run.

These results hold for the synthetic scenarios above, with a clean warm-up period and the baseline thresholds used here. They are not a claim about real production networks.

## Dashboard

The Streamlit dashboard provides:

- Scenario selection (S1 to S5)
- Adaptive z-threshold control
- Anomaly-score threshold control
- Repeated-run configuration
- Playback speed control for the live simulation
- Live anomaly-score visualization
- Baseline and proposed detector decisions
- Simulation summaries

## Project Structure

```text
network-anomaly-detector/
├── app.py
├── live_capture.py
├── make_graphs.py
├── run_evaluation.py
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── detectors.py
│   ├── evaluate.py
│   └── traffic.py
├── tests/
│   └── test_detectors.py
├── results/                 (generated locally by run_evaluation.py, not committed)
└── reports/
    ├── figures/
    └── project_structure.txt
```

## Installation

Create and activate a virtual environment.

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run the Dashboard

```powershell
streamlit run app.py
```

## Run the Evaluation

```powershell
python run_evaluation.py
```

Generate graphs (saved to `reports/figures`):

```powershell
python make_graphs.py
```

## Run the Tests

```powershell
python tests/test_detectors.py
```

## Optional Live Packet Capture

The optional `live_capture.py` script uses Scapy to collect network packet metadata. Live capture may require Npcap and administrator permissions on Windows.

Its third feature, stored under the key `failed_conn`, is the TCP SYN count per window, a lightweight connection-attempt proxy rather than a count of failed connections. Thresholds tuned on synthetic data may need re-tuning on real traffic.

Only monitor networks you own or are explicitly authorized to inspect.

## Limitations

- Evaluation uses synthetic rather than production network traffic.
- The adaptive detector assumes the 30-window warm-up contains only normal traffic. If an attack starts during warm-up, it is learned as normal.
- After a sudden permanent traffic shift, the adaptive detector keeps alerting, because alert windows are not used to update its profile.
- Attack windows that score just below the threshold can be gradually absorbed into the profile, which limits recall on quiet single-feature attacks (S5 recall is 0.78, not 1.0).
- On low-load traffic where the fixed thresholds already fit, the baseline is slightly more precise.
- Real packet capture depends on operating-system and interface support.
- The detector uses traffic metadata and does not inspect encrypted payload contents.
- Performance on real networks requires further testing and threshold tuning.

## Technologies

- Python
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Scapy (optional live capture)

## Project Outcome

The project implements and compares a fixed-threshold baseline and an adaptive statistical anomaly detector through an interactive dashboard and repeated-run evaluation, and reports where the adaptive approach helps and where it does not.