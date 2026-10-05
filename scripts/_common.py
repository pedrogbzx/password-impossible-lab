import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import load_config, validate_config


def configuration():
    config = load_config()
    validate_config(config)
    return config
