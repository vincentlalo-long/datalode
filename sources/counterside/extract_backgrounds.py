#!/usr/bin/env python3
# DataLode: Extract cutscene CGs and story backgrounds from CounterSide

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DEFAULT_BACKGROUNDS_DIR, get_default_streaming_dir
from modules.extractor.background_extractor import (
    clean_bg_name,
    extract_backgrounds,
    find_background_bundles,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DataLode: Extract high-resolution cutscene backgrounds and story CGs",
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        default="",
        help="Background name filter keyword (e.g. 'beach', 'academy', 'night')",
    )
    parser.add_argument(
        "-o", "--out",
        type=Path,
        default=DEFAULT_BACKGROUNDS_DIR,
        help=f"Output directory (default: {DEFAULT_BACKGROUNDS_DIR})",
    )
    parser.add_argument(
        "-d", "--game-dir",
        type=Path,
        default=None,
        help="Custom StreamingAssets folder path",
    )
    parser.add_argument(
        "--include-maps",
        action="store_true",
        help="Also extract ab_map_* battle environment maps",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List matching background bundles without extracting",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    streaming_dir = args.game_dir or get_default_streaming_dir()

    if not streaming_dir.is_dir():
        print(f"[!] Error: Directory not found: {streaming_dir}")
        return 1

    bundles = find_background_bundles(streaming_dir, include_maps=args.include_maps)
    if args.name:
        kw = args.name.lower().strip()
        bundles = [b for b in bundles if kw in b.name.lower()]

    if args.list:
        print(f"[*] Found {len(bundles)} background bundle(s) matching '{args.name or '<all>'}':")
        for b in bundles:
            print(f"    - {b.name} -> {clean_bg_name(b.name)}.png")
        return 0

    print(f"[*] Extracting {len(bundles)} background bundle(s) to '{args.out}'...")
    res = extract_backgrounds(
        streaming_dir=streaming_dir,
        output_dir=args.out,
        name_filter=args.name,
        include_maps=args.include_maps,
    )

    print(f"[OK] Extracted {res['extracted_images']} background image(s) from {res['total_bundles']} bundles in {res['elapsed_seconds']}s")
    print(f"     -> Manifest saved to: {res['manifest_file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
