# District Lab · New York

**[Open the interactive map →](https://kvngnsn.github.io/ny-redistricting-lab/)**

An open-source redistricting experiment: 26 New York congressional districts, equal population, geographic contiguity with two disclosed island exceptions, and a Democratic sweep as the search objective.

**Result:** the published 2024-focused map produces **26 Democratic leads out of 26** in the modeled 2024 presidential vote. Its weakest district is only **D +1.37 points**, compared with **D +12.68 statewide**. This is a constructed historical result, not 26 safe seats or a forecast.

| Published plan | D leads, 2024 president | Weakest 2024 margin | D leads, 2022 governor | Districts D in every source election | Population range |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2024 sweep | 26 / 26 | D +1.37 | 14 / 26 | 14 / 26 | 1 person |
| Historical stress search | 26 / 26 | D +0.70 | 15 / 26 | 15 / 26 | 1 person |
| 2024 adopted reference | 19 / 26 | R +24.83 | 14 / 26 | 13 / 26 | 2 people |

Both experimental maps have **23 districts at 776,971 residents** and **3 at 776,972**, with all 26 district cores connected. Two zero-population Liberty/Ellis Island blocks retain their official assignment. Water polygons count toward Census geographic contiguity; this is not a road-connectivity rule.

## Explore

- Switch among both experiments and the official reference.
- Compare **13 statewide contests spanning 2008–2024**.
- Click districts for population, margins and election history.
- Inspect **14,191** common historical voting units; explore a uniform vote-share swing.
- Download district results, map geometry and all **288,819** Census-block assignments.
- Open the public source credits, methodology and machine-readable validation.

The model includes **12,984** 2024 precinct features and **11.26 million** block × election × candidate-group values. Values below the source voting-unit level are **population-weighted estimates**, including split precincts. They are not observed block ballots. Historical variation and allocation uncertainty matter especially for narrow leads.

## Navigate the project

| Start here | Contents |
| --- | --- |
| [Methodology](docs/METHODOLOGY.md) | Geographic graph, population, allocation, objectives, exact finishing and limitations |
| [Run and reproduce](docs/REPRODUCE.md) | Local site, offline verification, exact replay and new searches |
| [Sources and public attribution](docs/SOURCES.md) | Every provider, source versions, certification differences and fingerprints |
| [Data licenses](docs/DATA-LICENSES.md) | Dataset-specific terms and excluded releases |
| [Research bundle](research/) | Full numerical model, search records and replay checkpoints |
| [Scripts](scripts/) | Download, prepare, search, balance, validate and export |
| [Website source](src/) | Static MapLibre explorer; no backend or API key |
| [Published data](public/data/) | Three maps, full assignments, summaries and validation |

```sh
npm ci
npm run dev
```

To verify every published district without downloading the large original geometries:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/verify_release.py
```

GitHub Actions validates the full numerical release, runs frontend tests, builds the static site and deploys to GitHub Pages. The map is also checked in an isolated desktop/mobile Chromium session.

## Credits and licenses

**Original code is [MIT](LICENSE). Election data and derived results have separate restrictions.** DRA historical data retains CC BY-SA 4.0 and its stated no-sale condition. NYT 2024 data and results are subject to C-UDA noncommercial terms. Those terms travel with published downloads; the repository's MIT license does not override them.

Data credits: **U.S. Census Bureau; New York LATFOR; Dave's Redistricting / Social Good Fund; Steve Gerontakis; John Mifflin; Ryne Rohla / Decision Desk HQ; Voting and Election Science Team; Benjamin J. Rosenblatt; The New York Times**, with county election boards and OpenElections credited in the source records. [Full attribution and version audit](docs/SOURCES.md).

“2024 Precinct-Level Election Results.” *The New York Times*, accessed November 16, 2026. [NYT source project](https://github.com/nytimes/presidential-precinct-map-2024).

Map rendering: **MapLibre GL JS**. Typography: **Public Sans**. Research methods draw on the redistricting recombination literature. [Software and research acknowledgments](THIRD_PARTY_NOTICES.md).

No optimality, electoral-safety or legal-adoptability claim is made. The published assignments are evidence of feasibility under the stated computational model and constraints.
