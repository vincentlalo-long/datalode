#!/usr/bin/env python3
# DataLode: Extract Gacha Banners, Recruitment Art, and Loading Wallpapers

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DEFAULT_BANNERS_DIR, get_default_streaming_dir
from modules.extractor.banner_extractor import (
    extract_banners,
    find_banner_bundles,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DataLode: Extract Gacha recruitment banners, loading wallpapers, and promo art",
    )
    parser.add_argument(
        "-c", "--category",
        choices=["all", "gacha", "loading", "promo"],
        default="all",
        help="Banner category filter (default: all)",
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        default="",
        help="Name filter keyword (e.g. 'awaken', 'hilde', 'event')",
    )
    parser.add_argument(
        "-o", "--out",
        type=Path,
        default=DEFAULT_BANNERS_DIR,
        help=f"Output directory (default: {DEFAULT_BANNERS_DIR})",
    )
    parser.add_argument(
        "-d", "--game-dir",
        type=Path,
        default=None,
        help="Custom StreamingAssets folder path",
    )
    parser.add_argument(
        "--min-size",
        type=int,
        default=150,
        help="Minimum pixel size to filter out small icons (default: 150)",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List matching banner bundles without extracting",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    streaming_dir = args.game_dir or get_default_streaming_dir()

    if not streaming_dir.is_dir():
        print(f"[!] Error: Directory not found: {streaming_dir}")
        return 1

    categories = find_banner_bundles(streaming_dir)

    if args.list:
        total = 0
        for cat, bundles in categories.items():
            if args.category != "all" and args.category != cat:
                continue
            matching = [b for b in bundles if not args.name or args.name.lower() in b.name.lower()]
            total += len(matching)
            print(f"[*] Category '{cat}': {len(matching)} bundle(s)")
            for b in matching[:10]:
                print(f"    - {b.name}")
            if len(matching) > 10:
                print(f"    ... and {len(matching) - 10} more")
        print(f"[*] Total matching: {total} bundle(s)")
        return 0

    print(f"[*] Extracting banners (category: {args.category}) to '{args.out}'...")
    res = extract_banners(
        streaming_dir=streaming_dir,
        output_dir=args.out,
        category_filter=args.category,
        name_filter=args.name,
        min_size=args.min_size,
    )

    print(f"[OK] Extracted {res['extracted_images']} artwork image(s) from {res['total_bundles']} bundles in {res['elapsed_seconds']}s")
    for cat, count in res["categories_summary"].items():
        print(f"     -> {cat.capitalize()}: {count} images")
    print(f"     -> Manifest saved to: {res['manifest_file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
