from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
DATA_DIR = ARTIFACTS / "data"
MODELS_DIR = ARTIFACTS / "models"
PRED_DIR = ARTIFACTS / "predictions"
REPORT_DIR = ARTIFACTS / "reports"
LOG_DIR = ROOT / "logs"

for d in [ARTIFACTS, DATA_DIR, MODELS_DIR, PRED_DIR, REPORT_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)
