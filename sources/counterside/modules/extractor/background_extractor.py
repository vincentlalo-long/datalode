from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from .decrypt import load_bundle


def clean_bg_name(bundle_name: str) -> str:
    name = bundle_name.lower()
    if name.endswith(".asset"):
        name = name[:-6]

    prefixes = [
        "ab_ui_nkm_ui_cutscen_bg_",
        "ab_ui_cutscen_bg_",
        "ab_map_game_",
        "ab_map_",
    ]
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
            break

    return name.strip("_")


def find_background_bundles(streaming_dir: Path, include_maps: bool = False) -> list[Path]:
    bundles = sorted(streaming_dir.glob("ab_ui_nkm_ui_cutscen_bg_*.asset"))
    if include_maps:
        bundles.extend(sorted(streaming_dir.glob("ab_map_*.asset")))
    return bundles


def extract_backgrounds(
    streaming_dir: Path,
    output_dir: Path,
    name_filter: str | None = None,
    include_maps: bool = False,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    bundles = find_background_bundles(streaming_dir, include_maps=include_maps)

    if name_filter:
        kw = name_filter.lower().strip()
        bundles = [b for b in bundles if kw in b.name.lower()]

    start_time = time.time()
    extracted_records: list[dict[str, Any]] = []
    failed_bundles: list[str] = []

    total = len(bundles)
    for idx, b_path in enumerate(bundles, start=1):
        clean_id = clean_bg_name(b_path.name)
        try:
            env = load_bundle(b_path)
            textures = [obj.read() for obj in env.objects if obj.type.name == "Texture2D"]
            if not textures:
                continue

            for t_idx, tex in enumerate(textures):
                img = tex.image
                # Handle single or multiple textures per bundle
                if len(textures) == 1:
                    filename = f"{clean_id}.png"
                else:
                    sub_name = tex.m_Name.lower().replace(b_path.stem.lower(), "").strip("_")
                    tag = sub_name if sub_name else f"{t_idx + 1}"
                    filename = f"{clean_id}_{tag}.png"

                dest_file = output_dir / filename
                img.save(dest_file)

                extracted_records.append({
                    "id": clean_id,
                    "filename": filename,
                    "width": img.width,
                    "height": img.height,
                    "bundle": b_path.name,
                })

        except Exception as e:
            failed_bundles.append(f"{b_path.name}: {e}")

        if idx % 100 == 0 or idx == total:
            print(f"  [{idx:4d}/{total}] Processed... ({len(extracted_records)} images saved)")

    # Save manifest
    manifest_data = {
        "source": "counterside",
        "total_images": len(extracted_records),
        "total_bundles_scanned": total,
        "include_maps": include_maps,
        "backgrounds": extracted_records,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

    elapsed = time.time() - start_time
    return {
        "total_bundles": total,
        "extracted_images": len(extracted_records),
        "failed_count": len(failed_bundles),
        "elapsed_seconds": round(elapsed, 2),
        "output_dir": str(output_dir),
        "manifest_file": str(manifest_path),
    }
