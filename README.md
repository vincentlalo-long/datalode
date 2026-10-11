# DataLode

Data mining from multiple sources. One folder per source under `sources/`,
mined data lands in `data/<source>/`. Nothing mined is committed.

## Sources

- `sources/counterside/` — Unity Spine assets: decrypt bundles (XOR header +
  UnityPy) into `.skel/.atlas/.png`, batch portraits, taxonomy + `manifest.json`,
  headless renders, loose-PNG atlas packer, cutscene CG backgrounds, Japanese
  voice acting packs, and interactive Story/Comic Reader.

## Data layout

```
data/<source>/
  outputs/      raw extracts
  dataset/      organized + manifest.json
  backgrounds/  high-res cutscene CGs and backgrounds
  voices/       Japanese voice lines (WAV)
  cutscenes/    assembled story chapters + interactive index.html reader
```

Current: `data/counterside/` — 1,041 characters, 783 backgrounds, 21,444 JP voices, 4,156 story chapters.

## Run

```bash
# deps per source
pip install -r sources/counterside/requirements.txt

# point at your sources
cp .env.example .env

# counterside pipeline (run from repo root)
python sources/counterside/extract.py --name "mina" --list
python sources/counterside/extract.py --name "illust_nkm_unit_c_yoo_mi_na.asset"
python sources/counterside/extract_portraits.py
python sources/counterside/process_dataset.py
python sources/counterside/render_fullbody.py -n hilde   # needs Chromium
python sources/counterside/pack_atlas.py --input <png_folder> --out <atlas_folder> --name <name>

# additional mining & stories
python sources/counterside/extract_backgrounds.py        # extract all 780+ cutscene CGs
python sources/counterside/extract_voices.py             # extract 21,000+ Japanese voice clips
python sources/counterside/build_stories.py              # build story chapters + web reader
python sources/counterside/serve_story.py                # launch browser and read stories offline
```


Paths default to `data/counterside/`; override with `OUTPUT_DIR` / `DATASET_DIR`
in `.env` (relative to repo root, or absolute).

## Notes

- Assets belong to their owners (e.g. Studiobside/Nexon). Bring your own files.
- Personal research only, no redistribution.
