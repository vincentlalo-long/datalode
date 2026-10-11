#!/usr/bin/env python3
# DataLode: Extract Japanese character voice acting from CounterSide

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DEFAULT_VOICES_DIR, get_default_streaming_dir
from modules.extractor.voice_extractor import (
    clean_voice_pack_name,
    extract_voices_jp,
    find_japanese_voice_bundles,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DataLode: Extract Japanese voice acting lines for CounterSide characters",
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        default="",
        help="Character or voice pack filter keyword (e.g. 'mina', 'hilde', 'jia')",
    )
    parser.add_argument(
        "-o", "--out",
        type=Path,
        default=DEFAULT_VOICES_DIR,
        help=f"Output directory (default: {DEFAULT_VOICES_DIR})",
    )
    parser.add_argument(
        "-d", "--game-dir",
        type=Path,
        default=None,
        help="Custom StreamingAssets folder path",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List matching Japanese voice packs without extracting",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    streaming_dir = args.game_dir or get_default_streaming_dir()

    if not streaming_dir.is_dir():
        print(f"[!] Error: Directory not found: {streaming_dir}")
        return 1

    bundles = find_japanese_voice_bundles(streaming_dir)
    if args.name:
        kw = args.name.lower().strip()
        bundles = [b for b in bundles if kw in b.name.lower()]

    if args.list:
        print(f"[*] Found {len(bundles)} Japanese voice pack(s) matching '{args.name or '<all>'}':")
        for b in bundles:
            print(f"    - {b.name} -> {clean_voice_pack_name(b.name)}")
        return 0

    print(f"[*] Extracting {len(bundles)} Japanese voice pack(s) to '{args.out}'...")
    res = extract_voices_jp(
        streaming_dir=streaming_dir,
        output_dir=args.out,
        name_filter=args.name,
    )

    print(f"[OK] Extracted {res['total_audio_files']} Japanese voice clip(s) from {res['total_packs']} packs in {res['elapsed_seconds']}s")
    print(f"     -> Manifest saved to: {res['manifest_file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
