#!/usr/bin/env python3
# orcust-spine: Reference Spine asset extractor for CounterSide

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DEFAULT_OUTPUT_DIR, get_default_streaming_dir
from modules.extractor import extract_spine_bundle, find_bundles

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="orcust-spine: Extract character Spine assets from CounterSide",
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        default="",
        help="Character or skin name keyword (e.g. 'mina', 'hilde', 'gaeun')",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List matching bundles without extracting",
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
    parser.add_argument(
        "--all",
        action="store_true",
        help="Extract all matches without limit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    streaming_dir = args.game_dir or get_default_streaming_dir()

    if not streaming_dir.is_dir():
        print(f"[!] Error: Directory not found: {streaming_dir}")
        print("[!] Check .env or specify path with --game-dir")
        return 1

    matched = find_bundles(streaming_dir, args.name)
    print(f"[*] Found {len(matched)} bundle(s) matching '{args.name or '<all>'}'")

    if not matched:
        return 0

    # List mode
    if args.list:
        for idx, p in enumerate(matched, start=1):
            tag = p.stem.replace("ab_unit_illust_", "")
            print(f"  [{idx:3d}] {tag:<45} ({p.stat().st_size // 1024} KB)")
        print(f"Total: {len(matched)} bundle(s). Run without --list to extract.")
        return 0

    # Determine targets
    targets = matched if (args.all or len(matched) == 1) else matched[:5]
    if len(matched) > 1 and not args.all:
        print(f"[*] Extracting first {len(targets)} of {len(matched)} matches (use --all to extract all):")

    args.out.mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    success = 0

    for p in targets:
        try:
            res = extract_spine_bundle(p, args.out)
            anims = f" | anims: {', '.join(res['animations'])}" if res['animations'] else ""
            print(f"[+] {res['character']} -> {res['output_dir']} ({len(res['files'])} files{anims})")
            success += 1
        except Exception as e:
            print(f"[!] Error extracting {p.name}: {e}")

    elapsed = time.time() - start_time
    print(f"[OK] Extracted {success}/{len(targets)} character(s) in {elapsed:.2f}s -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
