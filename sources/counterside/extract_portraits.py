#!/usr/bin/env python3
# orcust-spine: Extract official character portrait / face card images

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DEFAULT_OUTPUT_DIR, get_default_streaming_dir
from modules.extractor import extract_portraits

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="orcust-spine: Extract official character portrait/face cards from CounterSide",
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        default="",
        help="Character or skin keyword filter (e.g. 'mina', 'hilde', 'gaeun')",
    )
    parser.add_argument(
        "-o", "--out",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "-d", "--game-dir",
        type=Path,
        default=None,
        help="Custom StreamingAssets folder path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    streaming_dir = args.game_dir or get_default_streaming_dir()

    if not streaming_dir.is_dir():
        print(f"[!] Error: Directory not found: {streaming_dir}")
        return 1

    print(f"[*] Extracting portraits matching: '{args.name or '<all>'}'...")
    res = extract_portraits(
        streaming_dir=streaming_dir,
        output_dir=args.out,
        name_filter=args.name,
        sync_to_char_dirs=True,
    )

    print(f"[OK] Extracted {res['total_extracted']} portrait(s) in {res['elapsed_seconds']}s")
    print(f"     -> {res['synced_to_char_folders']} synced directly to character folders as 'portrait.png'")
    print(f"     -> All saved to {res['portraits_dir']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
