# Research artifacts

[Project overview](../README.md) · [Reproduction instructions](../docs/REPRODUCE.md) · [Data terms](../docs/DATA-LICENSES.md)

- `model-inputs.npz`: all 288,819 block IDs, population, modeled votes, exact adjacency, adopted assignments and crosswalks. Array schema is in the reproduction guide.
- `elections.json`: the 13 contests, their order and original statewide D/R/other totals.
- `coarse.npz`, `coarse-graph.npz`: connected search units and their block mapping.
- `checkpoints/`: the 2024 branch's initial coarse state, both unbalanced final states, and exact finishing patches. These preserve the replay boundary transparently.
- `recombination-log.json`: 600-round historical stress search.
- `recombination-sweep-log.json`: 300-round 2024 search.
- `balance-*-log.json`: final exact whole-block population finishing records.
- `geometry-audit.json`, `nyt-allocation-audit.json`: graph connectivity and spatial source-coverage checks.
- `sources.lock.json`: SHA-256 fingerprints for the six source downloads.
- `release-hashes.json`: fingerprints for the released model and site data. Refresh intentionally with `scripts/seal_release.py` after reviewing regenerated artifacts.

Logs document finite optimization runs. They are not samples from a uniform distribution of valid maps, and they do not prove that no better map exists. No individual voter records are included.
