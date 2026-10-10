from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .decrypt import load_bundle


def extract_portraits(
    streaming_dir: Path,
    output_dir: Path,
    name_filter: str | None = None,
    sync_to_char_dirs: bool = True,
) -> dict[str, Any]:
    bundle_path = streaming_dir / "ab_unit_face_card.asset"
    if not bundle_path.is_file():
        raise FileNotFoundError(f"Face card bundle not found: {bundle_path}")

    env = load_bundle(bundle_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    portraits_dir = output_dir / "portraits"
    portraits_dir.mkdir(parents=True, exist_ok=True)

    # Index existing character folders in output_dir
    char_folders = {}
    if sync_to_char_dirs and output_dir.is_dir():
        for d in output_dir.iterdir():
            if d.is_dir() and d.name != "portraits":
                char_folders[d.name.lower()] = d

    filter_kw = name_filter.lower().strip() if name_filter else None
    start_time = time.time()
    extracted = 0
    synced_to_folders = 0

    for obj in env.objects:
        if obj.type.name != "Texture2D":
            continue

        data = obj.read()
        raw_name = data.m_Name
        clean_name = raw_name.replace("AB_UNIT_FACE_CARD_", "").lower()

        if filter_kw and filter_kw not in clean_name and filter_kw not in raw_name.lower():
            continue

        try:
            img = data.image

            # 1. Save to global portraits directory
            img.save(portraits_dir / f"{clean_name}.png")
            extracted += 1

            # 2. Sync to individual character output directory if it exists
            if clean_name in char_folders:
                img.save(char_folders[clean_name] / "portrait.png")
                synced_to_folders += 1

        except Exception as e:
            print(f"[!] Error saving {raw_name}: {e}")

    elapsed = time.time() - start_time
    return {
        "total_extracted": extracted,
        "synced_to_char_folders": synced_to_folders,
        "portraits_dir": str(portraits_dir),
        "elapsed_seconds": round(elapsed, 2),
    }
