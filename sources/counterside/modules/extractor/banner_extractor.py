from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from .decrypt import load_bundle


IGNORE_TEXTURE_NAMES = {
    "cmn_glow", "cmn_flash", "cmn_flare", "cmn_lens", "boxline", "black", "white",
}


def classify_banner_bundle(filename: str) -> str:
    lower = filename.lower()
    if "loading" in lower:
        return "loading"
    if "contractbanner" in lower or "shop_banner" in lower or "contract" in lower:
        return "gacha"
    if "banner_home" in lower or "banner_package" in lower or "banner_common" in lower:
        return "promo"
    return "misc"


def find_banner_bundles(streaming_dir: Path) -> dict[str, list[Path]]:
    all_files = sorted(streaming_dir.glob("*.asset")) + sorted(streaming_dir.glob("*.jpn")) + sorted(streaming_dir.glob("*.eng"))
    categories: dict[str, list[Path]] = {
        "gacha": [],
        "loading": [],
        "promo": [],
    }

    for p in all_files:
        name = p.name.lower()
        if "contractbanner" in name or "shop_banner" in name:
            categories["gacha"].append(p)
        elif "ab_loading" in name and not name.endswith(".deu") and not name.endswith(".fra") and not name.endswith(".twn"):
            categories["loading"].append(p)
        elif name.startswith("banner_home") or name.startswith("banner_package") or name.startswith("banner_common"):
            categories["promo"].append(p)

    return categories


def extract_banners(
    streaming_dir: Path,
    output_dir: Path,
    category_filter: str = "all",
    name_filter: str | None = None,
    min_size: int = 150,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    categories = find_banner_bundles(streaming_dir)

    selected_bundles: list[tuple[str, Path]] = []
    for cat, bundles in categories.items():
        if category_filter != "all" and category_filter.lower() != cat:
            continue
        for b in bundles:
            if name_filter and name_filter.lower() not in b.name.lower():
                continue
            selected_bundles.append((cat, b))

    start_time = time.time()
    extracted_records: list[dict[str, Any]] = []
    seen_hashes: set[str] = set()

    total = len(selected_bundles)
    for idx, (cat, b_path) in enumerate(selected_bundles, start=1):
        cat_dir = output_dir / cat
        cat_dir.mkdir(parents=True, exist_ok=True)

        try:
            env = load_bundle(b_path)
            # Collect Sprites and Textures
            drawables: list[Any] = []
            sprites = [obj.read() for obj in env.objects if obj.type.name == "Sprite"]
            textures = [obj.read() for obj in env.objects if obj.type.name == "Texture2D"]

            # Prefer Sprites if available, otherwise Textures
            drawables = sprites if sprites else textures

            for d in drawables:
                name = getattr(d, "m_Name", "").strip()
                name_lower = name.lower()

                # Skip common FX / glow textures
                if any(ign in name_lower for ign in IGNORE_TEXTURE_NAMES):
                    continue

                img = getattr(d, "image", None)
                if img is None:
                    continue

                # Filter out tiny utility icons
                if img.width < min_size and img.height < min_size:
                    continue

                clean_name = re.sub(r"[^A-Za-z0-9_.-]+", "_", name).lower().strip("_")
                if not clean_name:
                    clean_name = b_path.stem.lower()

                filename = f"{clean_name}.png"
                dest_file = cat_dir / filename

                # Handle duplicate names within category
                dup_idx = 1
                while dest_file.exists():
                    dest_file = cat_dir / f"{clean_name}_{dup_idx}.png"
                    dup_idx += 1

                img.save(dest_file)
                extracted_records.append({
                    "id": clean_name,
                    "category": cat,
                    "filename": f"{cat}/{dest_file.name}",
                    "width": img.width,
                    "height": img.height,
                    "bundle": b_path.name,
                })

        except Exception:
            pass

        if idx % 50 == 0 or idx == total:
            print(f"  [{idx:3d}/{total}] Processed banner bundles... ({len(extracted_records)} images saved)")

    # Save manifest
    manifest_data = {
        "source": "counterside",
        "total_images": len(extracted_records),
        "total_bundles": total,
        "categories": {
            "gacha": sum(1 for r in extracted_records if r["category"] == "gacha"),
            "loading": sum(1 for r in extracted_records if r["category"] == "loading"),
            "promo": sum(1 for r in extracted_records if r["category"] == "promo"),
        },
        "banners": extracted_records,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

    elapsed = time.time() - start_time
    return {
        "total_bundles": total,
        "extracted_images": len(extracted_records),
        "categories_summary": manifest_data["categories"],
        "elapsed_seconds": round(elapsed, 2),
        "output_dir": str(output_dir),
        "manifest_file": str(manifest_path),
    }
