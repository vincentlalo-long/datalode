#!/usr/bin/env python3
# orcust-spine: Dataset filtering, renaming, and categorization

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DEFAULT_OUTPUT_DIR

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


@dataclass
class CharacterMetadata:
    id: str
    category: str
    sub_category: str
    clean_name: str
    source_dir: str
    files: list[str] = field(default_factory=list)
    has_skel: bool = False
    has_atlas: bool = False
    has_texture: bool = False
    has_fullbody: bool = False
    has_portrait: bool = False
    has_json: bool = False
    is_valid: bool = False
    animations: list[str] = field(default_factory=list)


# Detect animation names in .skel binary data
def detect_animations_from_skel(skel_path: Path) -> list[str]:
    try:
        content = skel_path.read_bytes()
        strings = [s.decode("latin1") for s in re.findall(rb"[A-Za-z0-9_-]{3,}", content)]
        keywords = ["idle", "touch", "talk", "action", "motion", "anim", "attack", "skill", "hit", "die"]
        return sorted({s for s in strings if any(k in s.lower() for k in keywords)})
    except Exception:
        return []


# Classify character folder into category, sub-category, and clean name
def classify_folder(folder_name: str) -> tuple[str, str, str]:
    lower = folder_name.lower().strip()

    # Bosses & Raids
    if "boss" in lower or "raid" in lower:
        sub = "raid" if "raid" in lower else "boss"
        clean = (
            lower.replace("nkm_monster_boss_", "")
            .replace("nkm_mob_boss_", "")
            .replace("nkm_npc_boss_", "npc_")
            .replace("nkm_monster_raid_", "raid_")
            .replace("nkm_npc_foolsday_", "")
        )
        return "boss", sub, clean

    # Operators
    if lower.startswith("opr_"):
        return "operator", "operator", lower.replace("opr_", "")

    # NPCs
    if lower.startswith("nkm_npc_"):
        return "npc", "npc", lower.replace("nkm_npc_", "")

    # Playable Units
    if lower.startswith("nkm_unit_"):
        parts = lower.split("_")
        clean = lower.replace("nkm_unit_", "")

        if "sd" in parts:
            sub = "sd"
        else:
            tokens = set(parts[2:])
            if tokens & {"c", "ca"}:
                sub = "counter"
            elif tokens & {"s", "sa"}:
                sub = "soldier"
            elif tokens & {"m", "ma"}:
                sub = "mecha"
            elif "trainer" in parts:
                sub = "trainer"
            else:
                sub = "unit"
        return "unit", sub, clean

    # Mobs / Regular Monsters
    if lower.startswith(("nkm_mob_", "nkm_monster_")):
        clean = lower.replace("nkm_mob_", "").replace("nkm_monster_", "")
        return "mob", "mob", clean

    return "other", "other", lower.replace("nkm_", "")


# Inspect folder contents and asset validity
def inspect_folder(folder_path: Path) -> CharacterMetadata:
    folder_name = folder_path.name
    category, sub_category, clean_name = classify_folder(folder_name)

    files = [f.name for f in folder_path.iterdir() if f.is_file()]
    skels = list(folder_path.glob("*.skel"))
    atlases = list(folder_path.glob("*.atlas"))
    textures = [p for p in folder_path.glob("*.png") if p.name not in ("full_body.png", "portrait.png")]
    has_fullbody = (folder_path / "full_body.png").is_file()
    has_portrait = (folder_path / "portrait.png").is_file()
    has_json = any(folder_path.glob("*.json"))

    has_skel = len(skels) > 0
    has_atlas = len(atlases) > 0
    has_texture = len(textures) > 0
    is_valid = has_skel and has_atlas and has_texture

    animations = detect_animations_from_skel(skels[0]) if skels else []

    return CharacterMetadata(
        id=folder_name,
        category=category,
        sub_category=sub_category,
        clean_name=clean_name,
        source_dir=str(folder_path),
        files=files,
        has_skel=has_skel,
        has_atlas=has_atlas,
        has_texture=has_texture,
        has_fullbody=has_fullbody,
        has_portrait=has_portrait,
        has_json=has_json,
        is_valid=is_valid,
        animations=animations,
    )


# Update texture filename reference in Spine atlas header
def patch_atlas_texture_reference(atlas_path: Path, old_tex_name: str, new_tex_name: str) -> None:
    try:
        content = atlas_path.read_text(encoding="utf-8")
        if old_tex_name in content:
            new_content = content.replace(old_tex_name, new_tex_name, 1)
            atlas_path.write_text(new_content, encoding="utf-8")
    except Exception as e:
        print(f"    [!] Warning: Failed to patch {atlas_path.name}: {e}")


# Copy, move, or symlink file
def copy_or_move_file(src: Path, dest: Path, mode: str) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        dest.unlink()

    if mode == "copy":
        shutil.copy2(src, dest)
    elif mode == "move":
        shutil.move(src, dest)
    elif mode == "symlink":
        dest.symlink_to(src.resolve())


# Process and reorganize single character
def process_character(
    meta: CharacterMetadata,
    dest_root: Path,
    mode: str,
    rename_generic: bool = True,
    rename_all_spine: bool = False,
    prefix_category: bool = False,
    clean_folder_name: bool = False,
    unit_subdirs: bool = True,
    split_units: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    src_dir = Path(meta.source_dir)

    # Determine category prefix
    if prefix_category:
        cat_tag = meta.sub_category if meta.category == "unit" else meta.category
        base_prefix = f"{cat_tag}_"
    else:
        base_prefix = ""

    folder_core = meta.clean_name if clean_folder_name else meta.id
    if base_prefix and folder_core.startswith(base_prefix):
        dest_folder_name = folder_core
    else:
        dest_folder_name = f"{base_prefix}{folder_core}"

    # Determine target directory
    if meta.category == "unit":
        if split_units:
            target_char_dir = dest_root / meta.sub_category / dest_folder_name
        elif unit_subdirs:
            target_char_dir = dest_root / "unit" / meta.sub_category / dest_folder_name
        else:
            target_char_dir = dest_root / "unit" / dest_folder_name
    else:
        target_char_dir = dest_root / meta.category / dest_folder_name

    operations: list[dict[str, str]] = []

    # Spine file prefix
    if base_prefix and meta.clean_name.startswith(base_prefix):
        file_prefix = meta.clean_name
    else:
        file_prefix = f"{base_prefix}{meta.clean_name}"

    main_skels = [f for f in sorted(src_dir.glob("*.skel")) if not f.stem.endswith("_BG")]
    orig_spine_prefix = main_skels[0].stem if main_skels else ""
    atlas_patches: list[tuple[Path, str, str]] = []

    for f_path in sorted(src_dir.iterdir()):
        if not f_path.is_file():
            continue

        filename = f_path.name
        new_filename = filename

        # Rename all spine files or generic files
        if rename_all_spine and f_path.suffix in (".skel", ".atlas", ".png", ".json") and filename not in ("full_body.png", "portrait.png"):
            stem = f_path.stem
            ext = f_path.suffix
            if orig_spine_prefix and stem.startswith(orig_spine_prefix):
                suffix_part = stem[len(orig_spine_prefix):]
                new_filename = f"{file_prefix}{suffix_part}{ext}"
            elif stem.startswith("UNIT_ILLUST_BASE"):
                suffix_part = stem[len("UNIT_ILLUST_BASE"):]
                new_filename = f"{file_prefix}{suffix_part}{ext}"
            elif stem.startswith("UNIT_ILLUST_"):
                new_filename = f"{file_prefix}{ext}"

            if ext == ".png":
                atlas_patches.append((target_char_dir / f"{Path(new_filename).stem}.atlas", filename, new_filename))

        elif rename_generic and filename.startswith("UNIT_ILLUST_BASE"):
            ext = f_path.suffix
            stem = f_path.stem
            suffix_part = stem[len("UNIT_ILLUST_BASE"):]
            new_filename = f"{file_prefix}{suffix_part}{ext}"

            if ext == ".png":
                atlas_patches.append((target_char_dir / f"{file_prefix}{suffix_part}.atlas", filename, new_filename))

        dest_file = target_char_dir / new_filename
        operations.append({
            "src": str(f_path),
            "dest": str(dest_file),
            "is_rename": (filename != new_filename),
            "old_name": filename,
            "new_name": new_filename,
        })

        if not dry_run:
            copy_or_move_file(f_path, dest_file, mode)

    # Patch atlas texture names
    if not dry_run:
        for atlas_file, old_tex, new_tex in atlas_patches:
            if atlas_file.is_file():
                patch_atlas_texture_reference(atlas_file, old_tex, new_tex)

    return {
        "id": meta.id,
        "category": meta.category,
        "dest_dir": str(target_char_dir),
        "files_count": len(operations),
        "renamed_files": [op for op in operations if op["is_rename"]],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="orcust-spine: Filter, rename, and organize Spine asset dataset",
    )
    parser.add_argument(
        "-s", "--src",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Source directory containing extracted assets (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "-d", "--dest",
        type=Path,
        default=ROOT_DIR / "dataset",
        help="Target dataset directory (default: ./dataset)",
    )
    parser.add_argument(
        "-c", "--categories",
        type=str,
        default="all",
        help="Comma-separated category filter (e.g. 'npc,unit,boss' or 'counter,soldier,mecha')",
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        default="",
        help="Filter by character name keyword",
    )
    parser.add_argument(
        "--exclude-sd",
        action="store_true",
        help="Exclude chibi/SD models (nkm_unit_sd_*)",
    )
    parser.add_argument(
        "--sd-only",
        action="store_true",
        help="Only include chibi/SD models",
    )
    parser.add_argument(
        "--valid-only",
        action="store_true",
        default=True,
        help="Only include valid folders with .skel, .atlas, and textures",
    )
    parser.add_argument(
        "--include-invalid",
        action="store_true",
        help="Include incomplete folders",
    )
    parser.add_argument(
        "--has-fullbody",
        action="store_true",
        help="Only include characters with full_body.png",
    )
    parser.add_argument(
        "--has-portrait",
        action="store_true",
        help="Only include characters with portrait.png",
    )
    parser.add_argument(
        "--mode",
        choices=["copy", "move", "symlink"],
        default="copy",
        help="Output mode: copy, move, or symlink (default: copy)",
    )
    parser.add_argument(
        "--prefix-category",
        action="store_true",
        help="Prefix category/sub-category on folder and filenames",
    )
    parser.add_argument(
        "--split-units",
        action="store_true",
        help="Separate counter, soldier, mecha into top-level directories",
    )
    parser.add_argument(
        "--no-unit-subdirs",
        action="store_true",
        help="Do not create subdirectories under unit/",
    )
    parser.add_argument(
        "--clean-names",
        action="store_true",
        default=True,
        help="Strip nkm_unit_ and nkm_npc_ prefixes (default: True)",
    )
    parser.add_argument(
        "--keep-raw-names",
        action="store_true",
        help="Keep raw folder names",
    )
    parser.add_argument(
        "--no-rename-generic",
        action="store_true",
        help="Do not rename generic UNIT_ILLUST_BASE.* files",
    )
    parser.add_argument(
        "--rename-all-spine",
        action="store_true",
        help="Rename all internal spine files to standardized character names",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate run without modifying files on disk",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="manifest.json",
        help="Manifest JSON filename in dest directory (default: manifest.json)",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Show dataset statistics and exit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src_dir = args.src

    if not src_dir.is_dir():
        print(f"[!] Directory not found: {src_dir}")
        return 1

    all_dirs = [d for d in sorted(src_dir.iterdir()) if d.is_dir() and d.name != "portraits"]
    metadata_list = [inspect_folder(d) for d in all_dirs]

    # Dataset statistics
    stats_raw = Counter([(m.category, m.sub_category) for m in metadata_list])
    stats_valid = Counter([(m.category, m.sub_category) for m in metadata_list if m.is_valid])
    stats_fullbody = sum(1 for m in metadata_list if m.has_fullbody)
    stats_portrait = sum(1 for m in metadata_list if m.has_portrait)
    stats_generic = sum(1 for m in metadata_list if any("UNIT_ILLUST_BASE" in f for f in m.files))

    display_order = [
        ("unit", "counter"),
        ("unit", "soldier"),
        ("unit", "mecha"),
        ("unit", "sd"),
        ("unit", "trainer"),
        ("npc", "npc"),
        ("boss", "boss"),
        ("boss", "raid"),
        ("operator", "operator"),
        ("mob", "mob"),
        ("other", "other"),
    ]

    print(f"[*] Total folders scanned: {len(metadata_list)}")
    print(f"{'Category':<10} | {'Sub-Category':<14} | {'Total':<6} | {'Valid':<6} | {'Ratio':<6}")
    print("-" * 52)
    for cat, sub in display_order:
        tot = stats_raw[(cat, sub)]
        val = stats_valid[(cat, sub)]
        if tot == 0:
            continue
        pct = f"{(val / tot * 100):.0f}%" if tot > 0 else "0%"
        print(f"{cat:<10} | {sub:<14} | {tot:<6} | {val:<6} | {pct:<6}")
    print("-" * 52)
    print(f"{'TOTAL':<27} | {len(metadata_list):<6} | {sum(stats_valid.values()):<6}")
    print(f"[*] full_body.png: {stats_fullbody}/{len(metadata_list)} | portrait.png: {stats_portrait}/{len(metadata_list)} | generic files: {stats_generic}")

    if args.stats_only:
        return 0

    # Filters
    filtered = metadata_list

    if args.categories != "all":
        selected_cats = {c.strip().lower() for c in args.categories.split(",") if c.strip()}
        filtered = [m for m in filtered if m.category in selected_cats or m.sub_category in selected_cats]

    if args.valid_only and not args.include_invalid:
        filtered = [m for m in filtered if m.is_valid]

    if args.exclude_sd:
        filtered = [m for m in filtered if m.sub_category != "sd"]
    elif args.sd_only:
        filtered = [m for m in filtered if m.sub_category == "sd"]

    if args.name:
        kw = args.name.lower().strip()
        filtered = [m for m in filtered if kw in m.id.lower() or kw in m.clean_name.lower()]

    if args.has_fullbody:
        filtered = [m for m in filtered if m.has_fullbody]

    if args.has_portrait:
        filtered = [m for m in filtered if m.has_portrait]

    if not filtered:
        print("[!] No characters match the filter criteria.")
        return 0

    after_filter_counts = Counter([(m.category, m.sub_category) for m in filtered])
    summary_parts = [f"{sub or cat}: {cnt}" for (cat, sub), cnt in sorted(after_filter_counts.items())]
    print(f"[*] Matched {len(filtered)} character(s) ({', '.join(summary_parts)})")

    rename_generic = not args.no_rename_generic
    clean_folder = args.clean_names and not args.keep_raw_names

    if not args.dry_run:
        args.dest.mkdir(parents=True, exist_ok=True)

    mode_tag = "DRY-RUN" if args.dry_run else args.mode.upper()
    print(f"[*] Processing ({mode_tag})...")

    results = []
    renamed_count = 0

    for idx, meta in enumerate(filtered, start=1):
        res = process_character(
            meta=meta,
            dest_root=args.dest,
            mode=args.mode,
            rename_generic=rename_generic,
            rename_all_spine=args.rename_all_spine,
            prefix_category=args.prefix_category,
            clean_folder_name=clean_folder,
            unit_subdirs=not args.no_unit_subdirs,
            split_units=args.split_units,
            dry_run=args.dry_run,
        )
        results.append(res)
        if res["renamed_files"]:
            renamed_count += 1

        if idx <= 3 or idx % 200 == 0 or idx == len(filtered):
            rel_dest = Path(res["dest_dir"]).relative_to(args.dest.parent if args.dest.parent.exists() else args.dest)
            tag = meta.sub_category.upper() if meta.category == "unit" else meta.category.upper()
            print(f"  [{idx:4d}/{len(filtered)}] [{tag:<7}] {meta.id} -> {rel_dest}")

    manifest_data = {
        "dataset_name": "orcust-spine-dataset",
        "total_characters": len(filtered),
        "categories_summary": {f"{k[0]}_{k[1]}": v for k, v in after_filter_counts.items()},
        "settings": {
            "source_dir": str(src_dir),
            "dest_dir": str(args.dest),
            "mode": args.mode,
            "prefix_category": args.prefix_category,
            "clean_folder_name": clean_folder,
            "rename_generic": rename_generic,
            "unit_subdirs": not args.no_unit_subdirs,
            "split_units": args.split_units,
            "dry_run": args.dry_run,
        },
        "characters": [asdict(m) for m in filtered],
    }

    if not args.dry_run:
        manifest_file = args.dest / args.manifest
        manifest_file.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"[OK] Saved manifest: {manifest_file}")

    print(f"[OK] Done. {len(filtered)} character(s) processed (renamed files: {renamed_count}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
