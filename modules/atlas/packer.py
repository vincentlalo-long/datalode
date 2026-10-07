from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from PIL import Image

try:
    from rectpack import newPacker
except ImportError:
    newPacker = None  # type: ignore


@dataclass
class PackedRegion:
    name: str
    src_path: Path
    orig_w: int
    orig_h: int
    trim_x: int
    trim_y: int
    trim_w: int
    trim_h: int
    atlas_x: int = 0
    atlas_y: int = 0
    trimmed_img: Image.Image | None = None


def _load_and_trim(png_path: Path) -> PackedRegion | None:
    """Load PNG, convert to RGBA, alpha-trim. Return None if fully transparent."""
    img = Image.open(png_path).convert("RGBA")
    orig_w, orig_h = img.size
    bbox = img.getbbox()
    if bbox is None:
        return None
    l, t, r, b = bbox
    trimmed = img.crop(bbox)
    return PackedRegion(
        name=png_path.stem,
        src_path=png_path,
        orig_w=orig_w,
        orig_h=orig_h,
        trim_x=l,
        trim_y=t,
        trim_w=r - l,
        trim_h=b - t,
        trimmed_img=trimmed,
    )


def _next_pow2(n: int) -> int:
    p = 1
    while p < n:
        p *= 2
    return p


def pack_layers(
    regions: Sequence[PackedRegion],
    atlas_size: int = 2048,
    padding: int = 2,
) -> tuple[int, int]:
    """Run MaxRects packing. Mutates regions with atlas_x/atlas_y. Returns used (w, h)."""
    if newPacker is None:
        raise RuntimeError("rectpack is required: pip install rectpack")

    # Deduplicate region names (Spine requires unique region names)
    seen: dict[str, int] = {}
    for r in regions:
        if r.name in seen:
            seen[r.name] += 1
            r.name = f"{r.name}_{seen[r.name]}"
        else:
            seen[r.name] = 0

    # Sort tallest first for better density (rectpack also sorts internally)
    ordered = sorted(regions, key=lambda r: r.trim_h, reverse=True)

    packer = newPacker(rotation=False)
    for r in ordered:
        packer.add_rect(r.trim_w + padding, r.trim_h + padding, rid=r.name)
    packer.add_bin(atlas_size, atlas_size)
    packer.pack()

    placed = {rect[5]: rect for rect in packer.rect_list()}
    if len(placed) != len(ordered):
        missing = [r.name for r in ordered if r.name not in placed]
        raise ValueError(
            f"Atlas overflow: {len(ordered) - len(placed)} region(s) do not fit "
            f"in {atlas_size}x{atlas_size}: {missing[:5]}. "
            f"Try --max-size 4096 or reduce input resolution."
        )

    max_x = max_y = 0
    by_name = {r.name: r for r in ordered}
    for _bin, x, y, _w, _h, rid in placed.values():
        r = by_name[rid]
        r.atlas_x = x
        r.atlas_y = y
        max_x = max(max_x, x + r.trim_w)
        max_y = max(max_y, y + r.trim_h)

    return max_x, max_y


def write_spine_atlas(
    atlas_path: Path,
    texture_filename: str,
    regions: Sequence[PackedRegion],
    page_w: int,
    page_h: int,
) -> None:
    """Write Spine libGDX plaintext atlas (compatible with Spine 3.7/3.8 runtime)."""
    lines = [
        texture_filename,
        f"size: {page_w},{page_h}",
        "format: RGBA8888",
        "filter: Linear,Linear",
        "repeat: none",
    ]
    for r in sorted(regions, key=lambda r: r.name):
        lines += [
            r.name,
            "  rotate: false",
            f"  xy: {r.atlas_x}, {r.atlas_y}",
            f"  size: {r.trim_w}, {r.trim_h}",
            f"  orig: {r.orig_w}, {r.orig_h}",
            f"  offset: {r.trim_x}, {r.trim_y}",
            "  index: -1",
        ]
    atlas_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def pack_png_folder(
    input_dir: Path,
    output_dir: Path,
    atlas_name: str = "atlas",
    atlas_size: int = 2048,
    padding: int = 2,
    pow2: bool = True,
) -> dict:
    """Pack all *.png in input_dir into <atlas_name>.png + <atlas_name>.atlas."""
    pngs = sorted(input_dir.glob("*.png"))
    if not pngs:
        raise FileNotFoundError(f"No PNG files found in: {input_dir}")

    regions: list[PackedRegion] = []
    skipped: list[str] = []
    for p in pngs:
        r = _load_and_trim(p)
        if r is None:
            skipped.append(p.name)
        else:
            regions.append(r)

    if not regions:
        raise ValueError(f"All {len(pngs)} PNG(s) are fully transparent.")

    used_w, used_h = pack_layers(regions, atlas_size=atlas_size, padding=padding)

    page_w = _next_pow2(used_w + padding) if pow2 else used_w + padding
    page_h = _next_pow2(used_h + padding) if pow2 else used_h + padding
    page_w = min(page_w, atlas_size)
    page_h = min(page_h, atlas_size)

    output_dir.mkdir(parents=True, exist_ok=True)
    texture_file = output_dir / f"{atlas_name}.png"
    atlas_file = output_dir / f"{atlas_name}.atlas"

    canvas = Image.new("RGBA", (page_w, page_h), (0, 0, 0, 0))
    for r in regions:
        assert r.trimmed_img is not None
        canvas.paste(r.trimmed_img, (r.atlas_x, r.atlas_y), r.trimmed_img)
    canvas.save(texture_file)

    write_spine_atlas(atlas_file, texture_file.name, regions, page_w, page_h)

    total_px = sum(r.trim_w * r.trim_h for r in regions)
    used_px = page_w * page_h
    return {
        "regions": len(regions),
        "skipped": skipped,
        "texture": str(texture_file),
        "atlas": str(atlas_file),
        "page": f"{page_w}x{page_h}",
        "efficiency": round(total_px / used_px * 100, 1) if used_px else 0.0,
        "region_names": sorted(r.name for r in regions),
    }
