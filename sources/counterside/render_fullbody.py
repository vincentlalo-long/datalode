#!/usr/bin/env python3
# orcust-spine: Headless Full-Body Standing Character Renderer

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import DEFAULT_OUTPUT_DIR
from modules.renderer import HeadlessRenderer, find_browser_executable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="orcust-spine: Render full-body standing illustrations from Spine data headlessly",
    )
    parser.add_argument(
        "-n", "--name",
        type=str,
        default="",
        help="Character name filter keyword (e.g. 'mina', 'hilde', 'gaeun')",
    )
    parser.add_argument(
        "-o", "--out",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Outputs directory (default: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Render all characters found in outputs directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-render even if full_body.png already exists",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    outputs_dir = args.out

    if not outputs_dir.is_dir():
        print(f"[!] Error: Outputs directory not found: {outputs_dir}")
        return 1

    try:
        browser_exe = find_browser_executable()
        print(f"[*] Headless browser engine: {browser_exe.name}")
    except FileNotFoundError as e:
        print(f"[!] Error: {e}")
        return 1

    # Scan available character folders
    candidates = []
    filter_kw = args.name.lower().strip() if args.name else ""

    for d in sorted(outputs_dir.iterdir()):
        if not d.is_dir() or d.name == "portraits":
            continue
        if filter_kw and filter_kw not in d.name.lower():
            continue

        has_skel = any(d.glob("*.skel"))
        has_atlas = any(d.glob("*.atlas"))
        if has_skel and has_atlas:
            candidates.append(d)

    if not candidates:
        print(f"[!] No matching character folders with Spine data found for: '{args.name}'")
        return 0

    targets = candidates if (args.all or len(candidates) == 1) else candidates[:5]
    if len(candidates) > 1 and not args.all:
        print(f"[*] Found {len(candidates)} matching characters. Rendering first {len(targets)} (use --all to render all):")
    else:
        print(f"[*] Rendering {len(targets)} character(s)...")

    renderer = HeadlessRenderer(outputs_dir)
    success = 0
    start_time = time.time()

    try:
        for idx, char_dir in enumerate(targets, start=1):
            out_img = char_dir / "full_body.png"
            if out_img.is_file() and not args.force:
                print(f"[{idx}/{len(targets)}] {char_dir.name} -> already exists (skip)")
                success += 1
                continue

            print(f"[{idx}/{len(targets)}] Rendering {char_dir.name}...", end="", flush=True)
            ok = renderer.render_character(char_dir.name, out_img)
            if ok and out_img.is_file():
                size_kb = out_img.stat().st_size // 1024
                print(f" -> OK ({size_kb} KB)")
                success += 1
            else:
                print(" -> FAILED")
    finally:
        renderer.close()

    elapsed = time.time() - start_time
    print(f"\n[OK] Rendered {success}/{len(targets)} character(s) in {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
