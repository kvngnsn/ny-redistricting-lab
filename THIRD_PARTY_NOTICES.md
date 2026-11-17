# Third-party acknowledgments

[Data sources and contributors](docs/SOURCES.md) · [Data license terms](docs/DATA-LICENSES.md) · [Full distributed software notices](public/notices/software.md)

The interactive map uses **MapLibre GL JS** (BSD-3-Clause; includes attributed Mapbox, glfx and d3-color code). **Public Sans**, from the U.S. Web Design System/Public Sans project, is distributed through Fontsource under the SIL Open Font License. Their original notices, plus all production dependency notices found in the pinned packages, ship with the website in `notices/software.md`. Regenerate that file with `node scripts/notices.mjs` after dependency changes.

The research tools use NumPy, SciPy, Numba/llvmlite, pandas, GeoPandas, Shapely/GEOS, Pyogrio/GDAL and pyproj/PROJ. These are installed from their own distributions through `requirements.txt`; they are not vendored or relicensed by this project. Their copyright and license notices remain in those distributions. Vite builds the frontend; Playwright/Chromium runs isolated UI checks.

Tree recombination is inspired by the redistricting literature: Daryl DeFord, Moon Duchin and Justin Solomon, [“Recombination: A family of Markov chains for redistricting”](https://arxiv.org/abs/1911.05725). This project's implementation is an objective-driven heuristic with different tree generation, acceptance and finishing rules. It is not a reproduction of a uniform ensemble or a claim about ensemble probabilities. No GerryChain source code is copied.

No source provider endorses the maps or their partisan objective. Original project code is [MIT](LICENSE). Election inputs and derived results retain the distinct restrictions documented in [Data licenses](docs/DATA-LICENSES.md).
