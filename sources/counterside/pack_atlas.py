#!/usr/bin/env python3
# pack Spine texture atlas from layered PNGs (see-through / PSD export output)

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from modules.atlas import pack_png_folder

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Pack layered PNGs into a single Spine .png + .atlas (Step 2 of image-to-spine)",
    )
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Input folder containing layered *.png (e.g. see-through output)",
    )
    parser.add_argument(
        "-o", "--out",
        type=Path,
        default=None,
        help="Output folder (default: <input>_atlas)",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="atlas",
        help="Atlas base name (default: atlas -> atlas.png + atlas.atlas)",
    )
    parser.add_argument(
        "--max-size",
        type=int,
        default=2048,
        choices=[1024, 2048, 4096],
        help="Max atlas page size (default: 2048)",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=2,
        help="Padding between regions to avoid edge bleeding (default: 2)",
    )
    parser.add_argument(
        "--no-pow2",
        action="store_true",
        help="Do not round page size up to power-of-two",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not args.input.is_dir():
        print(f"[!] Input directory not found: {args.input}")
        return 1

    out_dir = args.out or (args.input.parent / f"{args.input.name}_atlas")

    start = time.time()
    try:
        res = pack_png_folder(
            input_dir=args.input,
            output_dir=out_dir,
            atlas_name=args.name,
            atlas_size=args.max_size,
            padding=args.padding,
            pow2=not args.no_pow2,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        print(f"[!] Error: {e}")
        return 1

    elapsed = time.time() - start
    print(f"[+] Packed {res['regions']} region(s) -> {res['page']} (efficiency ~{res['efficiency']}%) in {elapsed:.2f}s")
    print(f"    texture: {res['texture']}")
    print(f"    atlas:   {res['atlas']}")
    if res["skipped"]:
        print(f"    skipped fully-transparent: {', '.join(res['skipped'])}")
    print(f"    regions: {', '.join(res['region_names'][:10])}" + (" ..." if len(res['region_names']) > 10 else ""))
    print(f"[OK] Done -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
