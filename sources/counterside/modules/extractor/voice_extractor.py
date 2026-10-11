from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from .decrypt import load_bundle


def clean_voice_pack_name(bundle_name: str) -> str:
    name = bundle_name.lower()
    if name.endswith(".vjpn"):
        name = name[:-5]

    prefixes = [
        "ab_ui_skin_voice_nkm_unit_",
        "ab_ui_unit_voice_nkm_unit_",
        "ab_ui_skin_voice_",
        "ab_ui_unit_voice_",
        "ab_npc_voice_",
        "ab_unit_illust_nkm_unit_",
        "ab_unit_illust_",
        "ab_sound_fx_",
        "ab_titlecall_",
        "ab_",
    ]
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
            break

    # Strip trailing _loc
    if name.endswith("_loc"):
        name = name[:-4]

    return name.strip("_")


def find_japanese_voice_bundles(streaming_dir: Path) -> list[Path]:
    bundles: list[Path] = []

    # 1. Dedicated voice directory
    voice_dir = streaming_dir / "voice"
    if voice_dir.is_dir():
        bundles.extend(sorted(voice_dir.glob("*.vjpn")))

    # 2. Root StreamingAssets
    bundles.extend(sorted(streaming_dir.glob("*.vjpn")))

    return bundles


def extract_voices_jp(
    streaming_dir: Path,
    output_dir: Path,
    name_filter: str | None = None,
) -> dict[str, Any]:
    output_jp_dir = output_dir / "jp"
    output_jp_dir.mkdir(parents=True, exist_ok=True)

    bundles = find_japanese_voice_bundles(streaming_dir)
    if name_filter:
        kw = name_filter.lower().strip()
        bundles = [b for b in bundles if kw in b.name.lower()]

    start_time = time.time()
    characters_info: dict[str, Any] = {}
    total_audio_files = 0
    failed_bundles: list[str] = []

    total_bundles = len(bundles)
    for idx, b_path in enumerate(bundles, start=1):
        clean_id = clean_voice_pack_name(b_path.name)
        char_dir = output_jp_dir / clean_id
        char_dir.mkdir(parents=True, exist_ok=True)

        char_clips: list[str] = []

        try:
            env = load_bundle(b_path)
            clips = [obj.read() for obj in env.objects if obj.type.name == "AudioClip"]

            for clip in clips:
                # clip.samples is a dict: { "sound_name.wav": bytes }
                samples = getattr(clip, "samples", {})
                if not samples:
                    continue

                for filename, audio_bytes in samples.items():
                    out_file = char_dir / filename
                    out_file.write_bytes(audio_bytes)
                    char_clips.append(filename)
                    total_audio_files += 1

            characters_info[clean_id] = {
                "bundle": b_path.name,
                "clip_count": len(char_clips),
                "folder": f"jp/{clean_id}",
            }

        except Exception as e:
            failed_bundles.append(f"{b_path.name}: {e}")

        if idx % 50 == 0 or idx == total_bundles:
            print(f"  [{idx:3d}/{total_bundles}] Extracted voice packs... ({total_audio_files} audio files saved)")

    # Save manifest
    manifest_data = {
        "language": "japanese",
        "total_packs": total_bundles,
        "total_audio_files": total_audio_files,
        "characters": characters_info,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

    elapsed = time.time() - start_time
    return {
        "total_packs": total_bundles,
        "total_audio_files": total_audio_files,
        "failed_count": len(failed_bundles),
        "elapsed_seconds": round(elapsed, 2),
        "output_dir": str(output_dir),
        "manifest_file": str(manifest_path),
    }
