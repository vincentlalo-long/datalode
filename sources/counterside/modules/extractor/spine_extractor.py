from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .decrypt import load_bundle, text_asset_bytes


# Detect animation names in .skel binary data
def detect_animations_from_skel(skel_bytes: bytes) -> list[str]:
    strings = [s.decode("latin1") for s in re.findall(rb"[A-Za-z0-9_-]{3,}", skel_bytes)]
    keywords = ["idle", "touch", "talk", "action", "motion", "anim", "attack", "skill"]
    return sorted({s for s in strings if any(k in s.lower() for k in keywords)})


# Find matching character Spine bundles in StreamingAssets
def find_bundles(
    streaming_dir: Path,
    name_filter: str | None = None,
    illust_only: bool = True,
) -> list[Path]:
    if not streaming_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {streaming_dir}")

    pattern = "ab_unit_illust_*.asset" if illust_only else "ab_unit_*.asset"
    bundles = list(streaming_dir.glob(pattern))

    if not name_filter:
        return sorted(bundles)

    query = name_filter.lower().strip()
    return sorted([p for p in bundles if query in p.name.lower()])


# Extract .skel, .atlas, .png from bundle into target folder
def extract_spine_bundle(
    bundle_path: Path,
    output_dir: Path,
) -> dict[str, Any]:
    env = load_bundle(bundle_path)

    folder_name = bundle_path.stem.replace("ab_unit_illust_", "").replace("ab_unit_", "")
    target_folder = output_dir / folder_name
    target_folder.mkdir(parents=True, exist_ok=True)

    extracted_files: list[str] = []
    animations: list[str] = []

    for obj in env.objects:
        if obj.type.name == "TextAsset":
            data = obj.read()
            raw_bytes = text_asset_bytes(data)
            out_file = target_folder / data.m_Name
            out_file.write_bytes(raw_bytes)
            extracted_files.append(out_file.name)

            if out_file.name.endswith(".skel"):
                animations.extend(detect_animations_from_skel(raw_bytes))

        elif obj.type.name == "Texture2D":
            data = obj.read()
            try:
                out_file = target_folder / f"{data.m_Name}.png"
                data.image.save(out_file)
                extracted_files.append(out_file.name)
            except Exception as e:
                print(f"Warning: Failed to save texture {data.m_Name}: {e}")

    if not extracted_files and target_folder.exists():
        try:
            target_folder.rmdir()
        except OSError:
            pass

    return {
        "bundle": bundle_path.name,
        "character": folder_name,
        "output_dir": str(target_folder),
        "files": extracted_files,
        "animations": sorted(set(animations)),
    }
