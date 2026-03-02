from __future__ import annotations

import os
from pathlib import Path


def app_data_dir() -> Path:
    base = os.getenv("APPDATA")
    if base:
        return Path(base) / "LoginSwitch"
    return Path.home() / ".loginswitch"
