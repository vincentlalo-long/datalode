# OmniSpine

Toolkit for poking at 2D Spine assets (CounterSide). Built for fun and learning.

## What it does

- `extract.py` — unpacks Unity bundles (XOR header + UnityPy) into `.skel/.atlas/.png`
- `extract_portraits.py` — batch-extracts portrait cards
- `process_dataset.py` — sorts folders, applies taxonomy, writes `manifest.json`
- `render_fullbody.py` — renders stills via headless Chrome + PixiJS (needs Chromium)
- `pack_atlas.py` — packs a folder of loose PNGs into `.png + .atlas`

Local corpus (not committed): 998 characters, 996 stills, 697 portraits.

## Run

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # point it at your game install

python extract.py --name "mina" --list
python process_dataset.py --input outputs --catalog
```

## Notes

- Game assets belong to Studiobside/Nexon. Bring your own files, nothing hosted here.
- Personal research only, no redistribution.
