# Project configuration
BASELINE_RATE = 80
BASELINE_UNIQUE_DST = 20
BASELINE_FAILED_CONN = 10

EWMA_ALPHA = 0.10
Z_THRESHOLD = 3.0
ANOMALY_THRESHOLD = 0.60

WARMUP_WINDOWS = 30      # windows used to learn the initial baseline
MIN_SPREAD = 1.0         # floor for the spread so z-scores never explode

WINDOW_SECONDS = 1
RANDOM_SEED = 42
