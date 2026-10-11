#!/usr/bin/env python3
# DataLode: Parse cutscene scripts and build interactive Story/Webtoon Viewer

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import (
    DEFAULT_BACKGROUNDS_DIR,
    DEFAULT_CUTSCENES_DIR,
    get_default_cutscene_json_dir,
)
from modules.extractor.cutscene_parser import parse_cutscene_file

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


HTML_VIEWER_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CounterSide Story & Comic Reader</title>
  <style>
    :root {
      --bg-dark: #0f1117;
      --bg-card: #181b24;
      --bg-card-hover: #222634;
      --accent: #3b82f6;
      --accent-glow: rgba(59, 130, 246, 0.4);
      --text-main: #f3f4f6;
      --text-sub: #9ca3af;
      --border: #2d3345;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg-dark);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      overflow-x: hidden;
    }
    header {
      background: rgba(24, 27, 36, 0.95);
      backdrop-filter: blur(10px);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 100;
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
    }
    .header-left { display: flex; align-items: center; gap: 16px; }
    .brand { font-weight: 700; font-size: 1.15rem; color: #fff; display: flex; align-items: center; gap: 8px; }
    .brand span { color: var(--accent); }
    .nav-btn {
      background: var(--bg-card);
      border: 1px solid var(--border);
      color: var(--text-main);
      padding: 6px 14px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.9rem;
      transition: all 0.2s;
    }
    .nav-btn:hover { background: var(--bg-card-hover); border-color: var(--accent); }
    .mode-switch {
      display: flex;
      background: #11131a;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 3px;
    }
    .mode-btn {
      padding: 6px 14px;
      border: none;
      background: transparent;
      color: var(--text-sub);
      cursor: pointer;
      font-size: 0.85rem;
      font-weight: 500;
      border-radius: 6px;
      transition: all 0.2s;
    }
    .mode-btn.active { background: var(--accent); color: #fff; box-shadow: 0 0 10px var(--accent-glow); }
    
    /* Layout */
    .app-container { display: flex; flex: 1; }
    
    /* Sidebar */
    .sidebar {
      width: 320px;
      background: var(--bg-card);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      height: calc(100vh - 58px);
      position: sticky;
      top: 58px;
      transition: transform 0.3s;
    }
    .sidebar-search { padding: 14px; border-bottom: 1px solid var(--border); }
    .sidebar-search input {
      width: 100%;
      background: #11131a;
      border: 1px solid var(--border);
      color: #fff;
      padding: 8px 12px;
      border-radius: 6px;
      outline: none;
    }
    .sidebar-search input:focus { border-color: var(--accent); }
    .sidebar-list { flex: 1; overflow-y: auto; padding: 12px; }
    .cat-title {
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--accent);
      letter-spacing: 0.5px;
      margin: 14px 8px 6px;
    }
    .chapter-item {
      padding: 8px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.88rem;
      margin-bottom: 3px;
      color: var(--text-sub);
      transition: all 0.15s;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .chapter-item:hover { background: var(--bg-card-hover); color: #fff; }
    .chapter-item.active { background: var(--accent); color: #fff; font-weight: 600; }
    
    /* Content Area */
    .content-area { flex: 1; padding: 30px; display: flex; flex-direction: column; align-items: center; }
    
    /* Webtoon / Comic Mode */
    .webtoon-container {
      width: 100%;
      max-width: 800px;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    .comic-panel {
      background: #151822;
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      position: relative;
      box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }
    .panel-bg {
      width: 100%;
      height: 280px;
      background-size: cover;
      background-position: center;
      position: relative;
    }
    .panel-bg::after {
      content: "";
      position: absolute;
      inset: 0;
      background: linear-gradient(180deg, rgba(21,24,34,0.1) 0%, rgba(21,24,34,0.85) 100%);
    }
    .panel-body {
      padding: 16px 20px 20px;
      margin-top: -60px;
      position: relative;
      z-index: 2;
    }
    .speaker-tag {
      display: inline-block;
      background: var(--accent);
      color: #fff;
      font-weight: 600;
      font-size: 0.8rem;
      padding: 3px 10px;
      border-radius: 4px;
      margin-bottom: 8px;
    }
    .dialogue-text {
      font-size: 1.05rem;
      line-height: 1.6;
      color: #e5e7eb;
      background: rgba(17, 19, 26, 0.85);
      backdrop-filter: blur(8px);
      padding: 14px 18px;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,0.08);
    }
    .sfx-tag {
      font-size: 0.75rem;
      color: #fbbf24;
      margin-top: 6px;
      font-style: italic;
    }

    /* Visual Novel Mode */
    .vn-container {
      width: 100%;
      max-width: 1080px;
      aspect-ratio: 16 / 9;
      background: #000;
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      position: relative;
      box-shadow: 0 8px 30px rgba(0,0,0,0.6);
      display: none;
      user-select: none;
    }
    .vn-bg {
      position: absolute;
      inset: 0;
      background-size: cover;
      background-position: center;
      transition: background-image 0.4s ease-in-out;
    }
    .vn-bg-overlay {
      position: absolute;
      inset: 0;
      background: linear-gradient(0deg, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0) 40%);
    }
    .vn-dialogue-box {
      position: absolute;
      bottom: 20px;
      left: 30px;
      right: 30px;
      background: rgba(15, 17, 23, 0.88);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.15);
      border-radius: 10px;
      padding: 20px 24px;
      cursor: pointer;
    }
    .vn-speaker {
      color: #60a5fa;
      font-weight: 700;
      font-size: 1.1rem;
      margin-bottom: 8px;
    }
    .vn-text {
      color: #fff;
      font-size: 1.15rem;
      line-height: 1.6;
      min-height: 54px;
    }
    .vn-controls {
      position: absolute;
      top: 16px;
      right: 16px;
      display: flex;
      gap: 8px;
      z-index: 10;
    }
    .vn-ctrl-btn {
      background: rgba(0,0,0,0.6);
      border: 1px solid rgba(255,255,255,0.2);
      color: #fff;
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
    }
    .vn-ctrl-btn:hover { background: var(--accent); }
    .vn-step-counter {
      position: absolute;
      bottom: 8px;
      right: 14px;
      color: var(--text-sub);
      font-size: 0.8rem;
    }
  </style>
</head>
<body>
  <header>
    <div class="header-left">
      <div class="brand">🎼 <span>CounterSide</span> Story Reader</div>
      <button class="nav-btn" id="prev-btn">◀ Prev</button>
      <button class="nav-btn" id="next-btn">Next ▶</button>
    </div>
    <div class="header-center">
      <h3 id="current-title" style="font-size: 1rem; font-weight: 500;">Select a Chapter</h3>
    </div>
    <div class="header-right">
      <div class="mode-switch">
        <button class="mode-btn active" id="btn-mode-comic">📜 Comic Strip</button>
        <button class="mode-btn" id="btn-mode-vn">🎮 Visual Novel</button>
      </div>
    </div>
  </header>

  <div class="app-container">
    <div class="sidebar">
      <div class="sidebar-search">
        <input type="text" id="search-input" placeholder="Search chapters / episodes...">
      </div>
      <div class="sidebar-list" id="chapter-list">
        <!-- Injected via JS -->
      </div>
    </div>

    <div class="content-area">
      <!-- Mode 1: Comic Strip -->
      <div class="webtoon-container" id="webtoon-view">
        <div style="text-align: center; color: var(--text-sub); margin-top: 40px;">
          Choose a chapter from the sidebar to begin reading.
        </div>
      </div>

      <!-- Mode 2: Visual Novel -->
      <div class="vn-container" id="vn-view">
        <div class="vn-bg" id="vn-bg"></div>
        <div class="vn-bg-overlay"></div>
        <div class="vn-controls">
          <button class="vn-ctrl-btn" id="vn-auto-btn">Auto: OFF</button>
          <button class="vn-ctrl-btn" id="vn-log-btn">Log</button>
        </div>
        <div class="vn-dialogue-box" id="vn-box">
          <div class="vn-speaker" id="vn-speaker">Speaker</div>
          <div class="vn-text" id="vn-text">Dialogue text goes here...</div>
          <div class="vn-step-counter" id="vn-counter">0 / 0</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let catalog = [];
    let currentChapter = null;
    let currentBeats = [];
    let vnIndex = 0;
    let autoInterval = null;
    let activeMode = 'comic';

    async function init() {
      try {
        const res = await fetch('catalog.json');
        catalog = await res.json();
        renderSidebar();
        if (catalog.length > 0) {
          loadChapter(catalog[0].id);
        }
      } catch (err) {
        console.error('Error loading catalog:', err);
      }
    }

    function renderSidebar(filter = '') {
      const listEl = document.getElementById('chapter-list');
      listEl.innerHTML = '';

      const grouped = {};
      catalog.forEach(item => {
        const title = (item.title || item.id).toLowerCase();
        if (filter && !title.includes(filter.toLowerCase()) && !item.category.toLowerCase().includes(filter.toLowerCase())) {
          return;
        }
        const key = item.category + ' — ' + item.arc;
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(item);
      });

      for (const [groupName, items] of Object.entries(grouped)) {
        const catEl = document.createElement('div');
        catEl.className = 'cat-title';
        catEl.textContent = groupName;
        listEl.appendChild(catEl);

        items.forEach(c => {
          const itemEl = document.createElement('div');
          itemEl.className = 'chapter-item' + (currentChapter && currentChapter.id === c.id ? ' active' : '');
          itemEl.textContent = c.title || c.id;
          itemEl.title = c.title || c.id;
          itemEl.onclick = () => loadChapter(c.id);
          listEl.appendChild(itemEl);
        });
      }
    }

    async function loadChapter(cid) {
      const info = catalog.find(c => c.id === cid);
      if (!info) return;

      currentChapter = info;
      document.getElementById('current-title').textContent = (info.arc ? info.arc + ' : ' : '') + (info.title || info.id);
      renderSidebar(document.getElementById('search-input').value);

      try {
        const res = await fetch(`chapters/${cid}.json`);
        const data = await res.json();
        currentBeats = data.beats || [];
        vnIndex = 0;

        if (activeMode === 'comic') {
          renderComicView();
        } else {
          renderVnView();
        }
      } catch (err) {
        console.error('Failed to load chapter JSON:', err);
      }
    }

    function renderComicView() {
      const container = document.getElementById('webtoon-view');
      container.innerHTML = '';

      currentBeats.forEach(b => {
        const panel = document.createElement('div');
        panel.className = 'comic-panel';

        const bgUrl = b.background ? `../backgrounds/${b.background}` : 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==';

        panel.innerHTML = `
          <div class="panel-bg" style="background-image: url('${bgUrl}');"></div>
          <div class="panel-body">
            <div class="speaker-tag">${b.speaker}</div>
            <div class="dialogue-text">${b.dialogue}</div>
            ${b.sound ? `<div class="sfx-tag">⚡ SFX: ${b.sound}</div>` : ''}
          </div>
        `;
        container.appendChild(panel);
      });
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function renderVnView() {
      if (currentBeats.length === 0) return;
      const b = currentBeats[vnIndex];

      const bgUrl = b.background ? `../backgrounds/${b.background}` : '';
      document.getElementById('vn-bg').style.backgroundImage = bgUrl ? `url('${bgUrl}')` : 'none';
      document.getElementById('vn-speaker').textContent = b.speaker;
      document.getElementById('vn-text').textContent = b.dialogue;
      document.getElementById('vn-counter').textContent = `${vnIndex + 1} / ${currentBeats.length}`;
    }

    function vnNext() {
      if (vnIndex < currentBeats.length - 1) {
        vnIndex++;
        renderVnView();
      } else if (autoInterval) {
        toggleAuto();
      }
    }

    function vnPrev() {
      if (vnIndex > 0) {
        vnIndex--;
        renderVnView();
      }
    }

    function toggleAuto() {
      const btn = document.getElementById('vn-auto-btn');
      if (autoInterval) {
        clearInterval(autoInterval);
        autoInterval = null;
        btn.textContent = 'Auto: OFF';
      } else {
        autoInterval = setInterval(vnNext, 3500);
        btn.textContent = 'Auto: ON';
      }
    }

    // Event Listeners
    document.getElementById('btn-mode-comic').onclick = () => {
      activeMode = 'comic';
      document.getElementById('btn-mode-comic').classList.add('active');
      document.getElementById('btn-mode-vn').classList.remove('active');
      document.getElementById('webtoon-view').style.display = 'flex';
      document.getElementById('vn-view').style.display = 'none';
      renderComicView();
    };

    document.getElementById('btn-mode-vn').onclick = () => {
      activeMode = 'vn';
      document.getElementById('btn-mode-vn').classList.add('active');
      document.getElementById('btn-mode-comic').classList.remove('active');
      document.getElementById('webtoon-view').style.display = 'none';
      document.getElementById('vn-view').style.display = 'block';
      renderVnView();
    };

    document.getElementById('vn-box').onclick = vnNext;
    document.getElementById('vn-auto-btn').onclick = (e) => { e.stopPropagation(); toggleAuto(); };

    window.onkeydown = (e) => {
      if (activeMode === 'vn') {
        if (e.code === 'Space' || e.code === 'ArrowRight') vnNext();
        if (e.code === 'ArrowLeft') vnPrev();
      }
    };

    document.getElementById('search-input').oninput = (e) => {
      renderSidebar(e.target.value);
    };

    document.getElementById('next-btn').onclick = () => {
      if (!currentChapter) return;
      const idx = catalog.findIndex(c => c.id === currentChapter.id);
      if (idx >= 0 && idx < catalog.length - 1) loadChapter(catalog[idx + 1].id);
    };

    document.getElementById('prev-btn').onclick = () => {
      if (!currentChapter) return;
      const idx = catalog.findIndex(c => c.id === currentChapter.id);
      if (idx > 0) loadChapter(catalog[idx - 1].id);
    };

    init();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="DataLode: Build offline interactive Story & Comic Reader from cutscenes",
    )
    parser.add_argument(
        "-s", "--src",
        type=Path,
        default=None,
        help="Source directory of cutscene JSON files",
    )
    parser.add_argument(
        "-o", "--out",
        type=Path,
        default=DEFAULT_CUTSCENES_DIR,
        help=f"Output cutscenes directory (default: {DEFAULT_CUTSCENES_DIR})",
    )
    parser.add_argument(
        "-b", "--bg-dir",
        type=Path,
        default=DEFAULT_BACKGROUNDS_DIR,
        help=f"Backgrounds directory (default: {DEFAULT_BACKGROUNDS_DIR})",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of cutscenes processed (0 for all)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    src_dir = args.src or get_default_cutscene_json_dir()

    if not src_dir.is_dir():
        print(f"[!] Error: Cutscene JSON directory not found: {src_dir}")
        return 1

    out_dir = args.out
    chapters_dir = out_dir / "chapters"
    chapters_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(src_dir.glob("*.json"))
    if args.limit > 0:
        json_files = json_files[:args.limit]

    print(f"[*] Parsing {len(json_files)} cutscene script(s) from '{src_dir}'...")
    start_time = time.time()

    catalog: list[dict[str, Any]] = []
    total_beats = 0

    for idx, jf in enumerate(json_files, start=1):
        parsed = parse_cutscene_file(jf, backgrounds_dir=args.bg_dir)
        if not parsed or parsed["total_beats"] == 0:
            continue

        cid = parsed["id"]
        # Save individual chapter JSON
        chapter_file = chapters_dir / f"{cid}.json"
        chapter_file.write_text(json.dumps(parsed, indent=2, ensure_ascii=False), encoding="utf-8")

        # Record entry for catalog
        catalog.append({
            "id": cid,
            "title": parsed["title"],
            "category": parsed["category"],
            "arc": parsed["arc"],
            "total_beats": parsed["total_beats"],
        })
        total_beats += parsed["total_beats"]

        if idx % 500 == 0 or idx == len(json_files):
            print(f"  [{idx:4d}/{len(json_files)}] Processed... ({len(catalog)} story chapters assembled)")

    # Save catalog.json
    catalog_path = out_dir / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")

    # Save index.html viewer
    viewer_path = out_dir / "index.html"
    viewer_path.write_text(HTML_VIEWER_TEMPLATE, encoding="utf-8")

    elapsed = time.time() - start_time
    print(f"[OK] Done in {elapsed:.2f}s!")
    print(f"     -> {len(catalog)} playable chapters assembled ({total_beats} dialogue beats).")
    print(f"     -> Story Reader ready at: {viewer_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
