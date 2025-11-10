import logging
from .config import LOG_DIR
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(LOG_DIR) / "pipeline.log"

def get_logger(name="pipeline"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.FileHandler(LOG_PATH)
        fmt = "%(asctime)s %(levelname)s %(message)s"
        formatter = logging.Formatter(fmt)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def render_template(s: str):
    return s.replace("{{date}}", datetime.now().strftime("%Y-%m-%d"))
