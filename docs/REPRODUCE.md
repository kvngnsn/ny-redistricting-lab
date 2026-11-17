# Run, verify, and extend

[Overview](../README.md) · [Methodology](METHODOLOGY.md) · [Sources and licenses](SOURCES.md)

## Website

Node 24 is tested. No API keys, backend or basemap account are needed.

```sh
npm ci
npm test
npm run dev
# Production static files:
npm run build
```

The relative Vite base supports GitHub project Pages. Public source/election attribution is embedded in the site and accompanying notices.

## Verify the published results offline

Python 3.9–3.12; the original computation used Python 3.9. This does not redownload the large Census geometry.

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/verify_release.py
```

`research/model-inputs.npz` contains all sorted block IDs, population, historical votes, the exact block graph, reference assignments and spatial crosswalks. Arrays contain no Python objects and can be read with `numpy.load(..., allow_pickle=False)`. Votes have shape `288819 × 13 × 3`; columns are Democratic candidate, Republican candidate, other. Election order is in `research/elections.json`. District labels in `.npy` are zero-based; public CSV labels are 1–26.

The validator checks every district, all source totals, exact checkpoint replay and SHA-256 release fingerprints. GitHub Actions runs it before publishing.

## Exactly replay the released assignments

```sh
.venv/bin/python scripts/replay.py
.venv/bin/python scripts/validate.py --require-constraints
```

The replay restores the complete analytical inputs and applies the published finishing patches to the unbalanced checkpoints. It reproduces the assignments exactly without relying on finishing tie-breaking or a particular CPU's random-number implementation.

Checkpoints are research inputs, not a claim that the script starts from a blank map. `sweep-search-start.npy` is the coarse historical-search state from which the 2024 branch began. The two `*-before-balance.npy` files are the final heuristic outputs before exact finishing. The initial exploratory warm-up is outside the exact replay boundary. Final assignment patches and independent verification make the released result fully inspectable.

## Run a new search

Restore the published inputs first. These commands produce a new experiment in `.cache`; they do not change the released site automatically.

```sh
.venv/bin/python scripts/replay.py
# Re-run the 2024 coarse search from its included start:
.venv/bin/python scripts/recombine.py --init sweep-search-start.npy --suffix experiment --election 24_PRES --rounds 300 --attempts 6000 --seed 12000
# Optional block refinement (choose a compute budget):
.venv/bin/python scripts/optimize.py --blocks --suffix experiment --election 24_PRES --epochs 20 --attempts 5000000 --seed 16000
# Exact integer finishing:
.venv/bin/python scripts/balance.py --name experiment
```

The published sweep uses the coarse search followed by exact finishing. The optional block refinement above starts a new experiment and is not part of its exact replay. Set `--election all` for the weakest-election objective. A finite run may fail the objective or finishing constraint; always run the independent validator before claiming success.

## Rebuild from original source bytes

Allow several GB of working space for full-resolution geometry and intermediates. The six source downloads total about 396 MB; processing can take minutes and depends on hardware.

```sh
.venv/bin/python scripts/prepare_geometry.py
.venv/bin/python scripts/prepare_votes.py
.venv/bin/python scripts/compare_prepared.py
.venv/bin/python scripts/replay.py
.venv/bin/python scripts/export_site.py --units
```

The source-preparation scripts enforce `research/sources.lock.json`. A mutable download that changes is rejected until its provenance and terms are reviewed explicitly. `prepare_geometry.py` creates exact adjacency from original Census polygons; `prepare_votes.py` conserves every input unit's D/R/other totals. To compare a fresh rebuild with the published model before replaying, compare its `blocks.npz`, `edges.npy` and `votes.npy` to `research/model-inputs.npz`.

`finalize.py` is a release-author tool: it reads balanced `.cache/sweep.npy` and `.cache/stress.npy`, matches labels to the reference, validates, and writes model/replay artifacts. `export_site.py` emits simplified maps, full assignments, summaries and logs. Regenerating a release requires deliberately refreshing `research/release-hashes.json` with `scripts/seal_release.py` after reviewing the changes. `export_site.py --reuse-geometry` can refresh metadata only when assignments and displayed geometries are unchanged.

## Browser checks

```sh
npx playwright install chromium
npm run build
npm run preview -- --port 4186
# In another terminal:
PREVIEW_URL=http://127.0.0.1:4186 node tests/browser.mjs
```

The isolated Chromium test exercises desktop/mobile layouts, selection, election and plan changes, population coloring, source overlays, swing, credits and audit dialogs. Screenshots go to ignored `qa/`. No existing browser profile is read.
