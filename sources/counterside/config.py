from __future__ import annotations

import os
from pathlib import Path

# Repo root (this file lives in <root>/sources/<name>/; data dirs stay at root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Load .env variables into os.environ
def load_env(env_file: Path | None = None) -> None:
    target = env_file or (BASE_DIR / ".env")
    if not target.is_file():
        return

    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


load_env()

STREAMING_DIR_STR = os.getenv("CS_STREAMING_ASSETS_DIR", "")
OUTPUT_DIR_STR = os.getenv("OUTPUT_DIR", "")
DATASET_DIR_STR = os.getenv("DATASET_DIR", "")

SOURCE_DATA_DIR = BASE_DIR / "data" / "counterside"

DEFAULT_OUTPUT_DIR = (
    Path(OUTPUT_DIR_STR) if Path(OUTPUT_DIR_STR).is_absolute()
    else (BASE_DIR / OUTPUT_DIR_STR if OUTPUT_DIR_STR else SOURCE_DATA_DIR / "outputs")
)
DEFAULT_DATASET_DIR = (
    Path(DATASET_DIR_STR) if Path(DATASET_DIR_STR).is_absolute()
    else (BASE_DIR / DATASET_DIR_STR if DATASET_DIR_STR else SOURCE_DATA_DIR / "dataset")
)
DEFAULT_BACKGROUNDS_DIR = SOURCE_DATA_DIR / "backgrounds"
DEFAULT_VOICES_DIR = SOURCE_DATA_DIR / "voices"
DEFAULT_CUTSCENES_DIR = SOURCE_DATA_DIR / "cutscenes"
DEFAULT_BANNERS_DIR = SOURCE_DATA_DIR / "banners"




# Get StreamingAssets path from .env or fallback
def get_default_streaming_dir() -> Path:
    if STREAMING_DIR_STR:
        return Path(STREAMING_DIR_STR)
    return Path(r"D:\Game\CounterSide\Game\CounterSide\Data\StreamingAssets")


CUTSCENE_JSON_DIR_STR = os.getenv("CS_CUTSCENE_JSON_DIR", "")


# Get cutscene JSON directory from .env or fallback
def get_default_cutscene_json_dir() -> Path:
    if CUTSCENE_JSON_DIR_STR:
        return Path(CUTSCENE_JSON_DIR_STR)
    return Path(r"D:\Game\CounterSide\Server\RevivalSide\gameplay-jsons\StreamingAssets\ab_script_cutscene\luac")

