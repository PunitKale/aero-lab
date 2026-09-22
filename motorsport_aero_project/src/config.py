"""Versioned configuration and reproducible artifact locations."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def load_config(path: Path | None = None) -> dict:
    """Load the explicit, user-editable model contract."""
    return json.loads((path or ROOT / "config/project.json").read_text())

CONFIG = load_config()
