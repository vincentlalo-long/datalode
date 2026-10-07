# 🏮 karakuri-forge

> **Generic 2D Spine Asset Pipeline: Extract, Pack, Catalog & Render — no GUI needed.**  
> *From encrypted Unity bundles or loose PNG layers to standardized Spine datasets and transparent renders.*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Spine](https://img.shields.io/badge/Spine-3.7%20%7C%203.8-orange.svg)](http://esotericsoftware.com/)
[![WebGL](https://img.shields.io/badge/Renderer-PixiJS%20%7C%20Headless%20WebGL-green.svg)](https://pixijs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Overview

**`karakuri-forge`** (formerly *orcust-spine / spine-headless-pipeline*) is a standalone toolkit for 2D skeletal-animation assets (**Spine 3.7 / 3.8**). It works in two independent directions:

1. **Game → Data:** decrypt Unity bundles, catalog characters, render transparent stills / driving videos.
2. **Layers → Spine:** pack loose layered PNGs (e.g. `see-through` output) into a standard `PNG + .atlas` pair for rigging and motion retargeting.

```text
       ┌────────────────────────────────────────────────────────┐
       │  A. Encrypted Game Bundles      B. Layered PNGs          │
       │     (Unity .asset files)           (see-through / PSD)   │
       └───────────────┬────────────────────────┬───────────────┘
                       │                        │
                       ▼                        ▼
       ┌────────────────────────────────────────────────────────┐
       │                    karakuri-forge                      │
       │                                                        │
       │  [1. Asset Extractor]     ──► .skel, .atlas, .png      │
       │  [2. Portrait Sync]       ──► 256x256 face cards       │
       │  [3. Dataset Normalizer]  ──► Tagged catalog + manifest│
       │  [4. Headless Renderer]   ──► Transparent PNGs / clips │
       │  [5. Atlas Packer]        ──► PNG layers → .png+.atlas │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                   Downstream (optional)                │
       │  - AI Vision / Motion-LoRA datasets                    │
       │  - Game modding, archival, web viewers                 │
       │  - karakuri-desk (desktop companion, Tauri + Python)   │
       └────────────────────────────────────────────────────────┘
```

`karakuri-desk` is **one** consumer of this pipeline, not its purpose. You can use forge without ever building a companion.

Part of the **Karakuri** ecosystem:
- **karakuri-forge** (this repo) — forges the body: assets, atlases, renders.
- **karakuri-desk** (planned) — houses the soul: transparent `idle/talk` loops + LLM/TTS on desktop.

---

## ✨ Key Features

- 🧩 **Asset Extraction (`extract.py`)**: Decrypts proprietary Unity packages (XOR 212-byte header + UnityPy). Extracts `.skel`, `.atlas`, `.png`. Reference corpus: *CounterSide* (1,300+ models), but the code is game-agnostic.
- 🎴 **Portrait Sync (`extract_portraits.py`)**: Batch-extracts face cards from UI bundles and mirrors them as `portrait.png` per character.
- 📊 **Dataset Normalizer (`process_dataset.py`)**:
  - Heuristic animation discovery in `.skel` binaries (`idle`, `touch`, `attack`, ...).
  - Rule-based taxonomy: `units` (counter/soldier/mecha), `bosses`, `raids`, `operators`, `NPCs`.
  - Emits `manifest.json` for batch jobs.
- 🎨 **Headless Renderer (`render_fullbody.py`)**:
  - Local HTTP server + headless Chromium/Edge + PixiJS Spine runtime. No external web server needed.
  - Dynamic bounds, auto-center, alpha-trim (`Pillow.getbbox()`).
  - Outputs `full_body.png` (~1200x2100 RGBA); extendable to short `idle.mp4` driving clips for motion transfer.
- 📦 **Atlas Packer (`pack_atlas.py` + `modules/atlas/packer.py`) — NEW**:
  - Input: folder of loose RGBA layers. Output: single `atlas.png + atlas.atlas` (Spine libGDX plaintext).
  - Alpha-trim, MaxRects bin-packing (`rectpack`), power-of-two pages, anti-bleed padding.
  - No GPU needed. Verified: 12 layers in 0.09s, no-overlap guarantee, clear overflow errors.

---

## 🚀 Quick Start

### 1. Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Chrome / Edge** (only for rendering)
- `pip install -r requirements.txt` (includes `UnityPy`, `Pillow`, `rectpack`, `tqdm`)

### 2. Configuration
```bash
cp .env.example .env
```

```env
CS_STREAMING_ASSETS_DIR=/path/to/game/StreamingAssets
OUTPUT_DIR=outputs
```

---

## 🛠️ CLI Usage

### A. Game → Data

```bash
# List bundles without extracting
python extract.py --name "c_yoo_mi_na" --list

# Extract
python extract.py --name "illust_nkm_unit_c_yoo_mi_na.asset"

# Portraits
python extract_portraits.py --sync

# Catalog & manifest
python process_dataset.py --input outputs --catalog

# Render
python render_fullbody.py -n hilde
python render_fullbody.py --all
python render_fullbody.py -n hilde --force
```

### B. Layers → Spine atlas

```bash
# Pack see-through / PSD-exported layers into Spine atlas
python pack_atlas.py --input kurisu_layers/ --out kurisu_atlas/ --name kurisu
# -> kurisu_atlas/kurisu.png + kurisu_atlas/kurisu.atlas

python pack_atlas.py --help
# --max-size {1024,2048,4096}  --padding 2  --no-pow2
```

---

## 💡 Use Cases (independent of any companion)

- **Modding & archival:** clean extraction + manifest for any Unity Spine title.
- **AI datasets:** stills + animation tags for vision models; driving clips for Motion-LoRA / LivePortrait.
- **Atlas tooling:** `pack_atlas.py` works on any OC / AI-generated character, no game needed.
- **Companion-ready (optional):** feed renders into `karakuri-desk` (Tauri transparent `<video>` + Python LLM/TTS state machine).

---

## ⚖️ Disclaimer

Built strictly for **educational, non-commercial, open-source research**.
- **No game assets, textures, or audio are hosted here.** `.gitignore` blocks `*.skel`, `*.atlas`, `*.asset`, `outputs/`, `dataset/`, `tools/*.exe`.
- All game assets belong to their owners (e.g. Studiobside / Nexon). Supply your own legally obtained files.

---

## 📜 License

Distributed under the [MIT License](LICENSE).
