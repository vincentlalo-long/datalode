from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

try:
    import UnityPy
except ImportError:
    UnityPy = None

ASSET_BUNDLE_HEADER_DECRYPT_SIZE = 212


# Generate 4 64-bit XOR keys from MD5 digest of bundle name
def get_bundle_masks(path: Path) -> list[int]:
    name = path.with_suffix("").name.lower()
    digest = hashlib.md5(name.encode("utf-8")).hexdigest()
    return [
        int(digest[0:16], 16),
        int(digest[16:32], 16),
        int(digest[0:8] + digest[16:24], 16),
        int(digest[8:16] + digest[24:32], 16),
    ]


# XOR decrypt / encrypt first 212 bytes of UnityFS bundle
def transform_bundle_header(data: bytes, path: Path) -> bytes:
    data = bytearray(data)
    masks = get_bundle_masks(path)
    mask_index = 0
    offset = 0
    size = min(len(data), ASSET_BUNDLE_HEADER_DECRYPT_SIZE)

    while offset < size:
        mask = masks[mask_index]
        remaining = size - offset
        if remaining >= 8:
            value = int.from_bytes(data[offset : offset + 8], "little") ^ mask
            data[offset : offset + 8] = value.to_bytes(8, "little")
            offset += 8
        else:
            low_byte = mask & 0xFF
            for index in range(offset, size):
                data[index] ^= low_byte
            offset = size

        mask_index = (mask_index + 1) % len(masks)

    return bytes(data)


# Read file and return decrypted header bytes
def decrypt_bundle_header(path: Path) -> bytes:
    return transform_bundle_header(path.read_bytes(), path)


# Load decrypted bundle into UnityPy Environment
def load_bundle(path: Path) -> Any:
    if UnityPy is None:
        raise RuntimeError("UnityPy is required: pip install UnityPy")
    return UnityPy.load(decrypt_bundle_header(path))


# Extract raw bytes from TextAsset
def text_asset_bytes(text_asset: Any) -> bytes:
    script = getattr(text_asset, "m_Script", b"")
    if isinstance(script, bytes):
        return script
    return script.encode("utf-8", "surrogateescape")
