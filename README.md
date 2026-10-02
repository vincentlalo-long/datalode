# 🎼 spine-headless-pipeline

> **Automated 2D Spine Asset Decryption, Dataset Normalization & Headless WebGL Rendering Engine.**  
> *A high-throughput CLI pipeline to extract, classify, and render Spine 2D skeletal assets without a graphical interface.*

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Spine](https://img.shields.io/badge/Spine-3.7%20%7C%203.8-orange.svg)](http://esotericsoftware.com/)
[![WebGL](https://img.shields.io/badge/Renderer-PixiJS%20%7C%20Headless%20WebGL-green.svg)](https://pixijs.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📖 Overview

**`spine-headless-pipeline`** (formerly *orcust-spine*) is a standalone engineering toolkit designed to reverse-engineer, parse, catalog, and render 2D binary skeletal animation assets (**Spine 3.7 / 3.8**) extracted from game client bundles.

The pipeline automates the entire journey from encrypted Unity asset archives to standardized character datasets and ultra-high-resolution, alpha-trimmed transparent standing illustrations.

```text
       ┌────────────────────────────────────────────────────────┐
       │             Encrypted Game Client Bundles              │
       │                 (Unity .asset files)                   │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                 spine-headless-pipeline                │
       │                                                        │
       │  [1. Asset Extractor]     ──► .skel, .atlas, .png      │
       │  [2. Portrait Sync]       ──► Official 256x256 cards   │
       │  [3. Dataset Normalizer]  ──► 1,300+ Tagged Characters │
       │  [4. Headless Renderer]   ──► 2K Transparent RGBA PNGs │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │                   Downstream Targets                   │
       │  - AI Vision / Multimodal Dataset Training             │
       │  - 2D Game Modding & Animation Research                │
       │  - Real-time Interactive WebGL & Desktop Visualizers   │
       └────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

- 🧩 **Automated Asset Extraction (`extract.py`)**: Decrypts and unpacks proprietary Unity game packages. Extracts binary skeleton files (`.skel`), texture atlas mappings (`.atlas`), and high-resolution sprite textures (`.png`). Tested against *CounterSide* as the reference corpus (1,300+ character and skin models).
- 🎴 **Face Card & Portrait Synchronizer (`extract_portraits.py`)**: Batch-extracts official square portraits directly from UI asset bundles and maps them to their respective character directories automatically.
- 📊 **Dataset Normalization & Binary Inspection (`process_dataset.py`)**:
  - Scans raw binary `.skel` data to automatically discover animation tracks (`idle`, `touch`, `attack`, `special`, etc.).
  - Classifies entities into structured taxonomies: `units` (counters, soldiers, mechas), `bosses`, `raids`, `operators`, and `NPCs`.
  - Generates JSON metadata registries for automated batch processing.
- 🎨 **Headless WebGL Rendering Engine (`render_fullbody.py`)**:
  - Powered by headless Chromium/Edge and PixiJS with the Spine WebGL runtime.
  - Generates crisp full-body standing illustrations (~1200x2100+) in pure RGBA format.
  - Automatically computes dynamic character bounding boxes, centers coordinates, and trims transparent alpha margins without requiring a local web server or manual human adjustment.

---

## 🚀 Quick Start

### 1. Prerequisites & Environment

- **Python 3.10+** (Python 3.11 recommended)
- **Google Chrome** or **Microsoft Edge** (utilized for headless WebGL rendering)

Install Python dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Copy `.env.example` to `.env` and specify your game client directory:
```bash
cp .env.example .env
```

Edit `.env`:
```env
CS_STREAMING_ASSETS_DIR=/path/to/game/StreamingAssets
OUTPUT_DIR=outputs
```

---

## 🛠️ CLI Pipeline Usage

### Step 1: Extract Spine Assets
Extract `.skel`, `.atlas`, and texture `.png` files from game bundles:
```bash
# Search and list matching character bundles without extracting
python extract.py --name "c_yoo_mi_na" --list

# Extract character Spine assets
python extract.py --name "illust_nkm_unit_c_yoo_mi_na.asset"
```

### Step 2: Extract & Synchronize Portraits
Extract official 256x256 face cards and mirror them to character folders:
```bash
python extract_portraits.py --sync
```
*Outputs are saved to `outputs/portraits/` and mirrored to each character's directory as `portrait.png`.*

### Step 3: Catalog & Classify Dataset
Audit character integrity, detect animation tracks, and organize metadata:
```bash
# Analyze extracted assets and generate character metadata
python process_dataset.py --input outputs --catalog
```

### Step 4: Headless Full-Body Rendering
Render Spine data into transparent RGBA PNGs:
```bash
# Render specific characters by name keyword
python render_fullbody.py -n hilde
python render_fullbody.py -n yoo_mi_na

# Render all extracted characters in batch
python render_fullbody.py --all

# Force re-rendering existing images
python render_fullbody.py -n hilde --force
```

---

## 📁 Output Dataset Structure

```text
outputs/
├── nkm_unit_c_hilde/
│   ├── UNIT_ILLUST_C_HILDE.skel   # Spine 3.7 binary skeleton data
│   ├── UNIT_ILLUST_C_HILDE.atlas  # Spine texture atlas definition
│   ├── UNIT_ILLUST_C_HILDE.png    # Sprite atlas texture sheet
│   ├── portrait.png               # Official 256x256 character face card
│   └── full_body.png              # Rendered transparent full-body art (~1200x2100)
├── portraits/                     # Central repository of extracted face cards
└── metadata.json                  # Normalized catalog with animation tags
```

---

## 💡 Practical Applications

- **Game Modding & Asset Archival**: Preservation and structural analysis of 2D game animations.
- **AI Vision Datasets**: Automated pipeline to generate ground-truth character illustrations with pose and animation tags for training generative models.
- **Virtual Avatars & Desktop Daemons**: Providing clean, lightweight motion assets and rendered sprites for interactive desktop runtimes.

---

## ⚖️ Disclaimer

This repository is developed strictly for **educational, non-commercial, and open-source research purposes**.
- **No copyrighted game assets, binary textures, or commercial audio clips are hosted or distributed in this repository.**
- All third-party game assets belong to their respective copyright holders (Studiobside Co., Ltd. / Nexon). Users are solely responsible for supplying their own legally acquired assets.

---

## 📜 License

Distributed under the [MIT License](LICENSE).