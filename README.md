# DataLode

Data mining from multiple sources. One folder per source under `sources/`,
mined data lands in `data/<source>/`. Nothing mined is committed.

## Sources

- `sources/counterside/` — Unity Spine assets: decrypt bundles (XOR header +
  UnityPy) into `.skel/.atlas/.png`, batch portraits, taxonomy + `manifest.json`,
  headless renders, loose-PNG atlas packer.

## Data layout

```
data/<source>/
  outputs/   raw extracts
  dataset/   organized + manifest.json
```

Current: `data/counterside/` — 998 characters, 996 stills, 697 portraits (~6GB).

## Run

```bash
# deps per source
pip install -r sources/counterside/requirements.txt

# point at your sources
cp .env.example .env

# counterside pipeline (run from repo root)
python sources/counterside/extract.py --name "mina" --list
python sources/counterside/extract.py --name "illust_nkm_unit_c_yoo_mi_na.asset"
python sources/counterside/extract_portraits.py --sync
python sources/counterside/process_dataset.py --catalog
python sources/counterside/render_fullbody.py -n hilde   # needs Chromium
python sources/counterside/pack_atlas.py --input <png_folder> --out <atlas_folder> --name <name>
```

Paths default to `data/counterside/`; override with `OUTPUT_DIR` / `DATASET_DIR`
in `.env` (relative to repo root, or absolute).

## Notes

- Assets belong to their owners (e.g. Studiobside/Nexon). Bring your own files.
- Personal research only, no redistribution.
