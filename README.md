# Real-Time Network Attack / Anomaly Detector

## Project objective
Detect suspicious network behaviour in real time and compare a fixed-threshold baseline with an adaptive detector.

## Proposed novelty
The proposed detector:
1. learns a normal traffic profile during warm-up,
2. adapts the profile using EWMA updates only on normal windows,
3. calculates z-score based deviations,
4. combines packet-rate, destination-diversity and failed-connection signals using weights,
5. exposes thresholds as runtime parameters.

## Scenarios
- S1: low load
- S2: medium load
- S3: high load

The evaluation uses synthetic traffic so the project can be demonstrated safely and reproducibly without generating real attacks.

## Setup
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Run dashboard
```bash
streamlit run app.py
```

## Run repeated evaluation
```bash
python run_evaluation.py
```


## Optional real-time packet capture
For an actual network-interface demonstration, install Scapy and (on Windows) Npcap.
Then run:
```bash
python live_capture.py
```
Run the terminal with the permissions required by your OS/Npcap setup. The script uses
packet metadata only: packet rate, unique destination IP count, and TCP SYN count.
Do not monitor networks you are not authorized to inspect.

## Git
```bash
git init
git add .
git commit -m "Initial network anomaly detector"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/network-anomaly-detector.git
git push -u origin main
```

## Rubric mapping
- Implementation & novelty: baseline + adaptive weighted anomaly score.
- Performance: S1/S2/S3, repeated runs, mean/SD, F1/precision/recall/FP.
- Demo: live simulation, baseline vs proposed, runtime parameter controls.
- Code explanation/viva: modular files and clear pipeline.
- Project document: methodology, results, graphs, limitations and outcome.
