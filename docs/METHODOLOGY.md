# Methodology

[Explore the map](https://kvngnsn.github.io/ny-redistricting-lab/) · [Overview](../README.md) · [Sources](SOURCES.md) · [Reproduce](REPRODUCE.md)

## Question and scope

Can a 26-district New York map produce a Democratic sweep with contiguous districts and equal population? This release evaluates two searches: **2024 presidential sweep** and **worst historical margin across 13 elections**. The 2024 result is evaluated against every older election too. No result is a forecast or proof of global optimality.

A statewide Democratic majority does not by itself prove that all districts can equal the statewide margin. The statewide two-party margin is a **vote-weighted** average of district margins. Equal population does not imply equal turnout. Geographic connectivity and indivisible blocks further restrict feasible partitions. Our search demonstrates its published assignments and metrics only; failure to find a stronger map would not prove impossibility.

## Geographic and population model

- All **288,819** New York 2020 Census blocks, including water blocks, appear exactly once.
- Population is unadjusted Census `POP20`: **20,201,249** residents. This follows LATFOR's congressional-data guidance; see [sources](SOURCES.md).
- The best possible integer equality is **23 districts × 776,971** and **3 × 776,972**. People and Census blocks are never subdivided.
- Blocks are adjacent only if their original Census polygons have disjoint interiors and a boundary intersection of dimension one: DE-9IM `F***1****`. Corner-only contacts do not connect districts. The resulting graph has **712,436** undirected edges.
- Census water polygons participate in this definition. Thus geographic contiguity here is not a claim that one can walk or drive between every point without crossing water.
- The graph has a main component containing all population and two isolated, zero-population blocks: **360610001001000** (part of Ellis Island) and **360610001001001** (Liberty Island). They retain the adopted district 10 assignment. These are the only approved exceptions. There are no invented bridge or nearest-neighbor edges.

Validation requires each district's remaining graph to have exactly one component. Strict contiguity with no exceptions is explicitly false. After optimization, district numbers are matched to the adopted districts by maximizing population overlap, using a linear assignment algorithm; this only renames districts. Island assignments are restored to 10.

The official reference is LATFOR's February 28, 2024 block assignment. Under this exact Census input its largest population difference is **2 people**. We preserve the reference as published and show that difference, rather than silently repairing it.

## Election panel and splits

The panel contains 13 statewide contests from **2008–2024**, across 12 historical contests in DRA v05 and the NYT 2024 presidential precinct file. It uses **14,191** historical VTD records and **12,984** 2024 precinct features. Congressional elections and synthetic composites are excluded. The latest election in this release is 2024; there is no 2026 election dataset here.

Historical votes have already been harmonized by DRA onto 2020 VTD geography. We join Census blocks to those VTDs through the Census block-assignment file. We allocate each VTD's Democratic-candidate, Republican-candidate and other counts proportional to its blocks' 2020 population. Zero-population source groups use land-area weights, with a minimum weight of one. Largest-remainder rounding preserves each source count exactly; ties use sorted Census-block order.

For 2024, each block is matched to the precinct containing its Census internal point. Unmatched blocks use the largest positive polygon overlap. A source precinct that otherwise has no block receives its largest overlapping available block without orphaning another source. Overlap area is calculated in the source longitude/latitude coordinates and used only to rank local overlaps. The crosswalk compares those coordinates directly; small datum differences and boundary-vintage errors are not modeled. All votes are then allocated with the same population-weighted rounding. This is a practical geographic crosswalk, not an exact historical voter-location reconstruction.

The 2024 source geometry does not cover **400 blocks containing 3,993 Census residents**. Those blocks receive no modeled source votes; this is missing coverage, not evidence of zero turnout. Every supplied precinct's source votes are allocated. All 13 statewide D/R/other totals are conserved. Source discrepancies from certified totals remain visible in the [source audit](SOURCES.md); we do not rescale counts to hide them.

**Split-precinct votes are estimates.** Moving blocks within a precinct permits district boundaries to split that precinct; it does not create observed block-level ballots. This assumption is especially consequential for a deliberately optimized, intricately shaped map. Population does not measure turnout or partisan preference within a precinct. Integer rounding, mismatched vintage, incomplete source geography and prior DRA harmonization add uncertainty. No error bounds or claim of electoral safety follow from these estimates.

## Search

1. Start from the official assignment. Form coarse units as connected components of blocks sharing a VTD and reference district. Every such unit is internally connected.
2. Explore single-unit boundary moves and two-district tree recombinations. A boundary move must preserve the donor's connectivity and attach to the recipient. Recombination merges neighboring districts, builds a randomized spanning tree and considers balanced cuts; this is an optimization heuristic, **not a uniform ensemble sampler**.
3. For the 2024 search, minimize `sum(exp(-25 × margin[d,2024]))`. For the historical stress search, replace that margin with the minimum across the 13 elections for each district. Margin here is `(D−R)/(D+R)`. This soft objective emphasizes weak districts without claiming to solve an exact max-min program.
4. Add `10,000 × sum(((population[d]−ideal)/ideal)^2)` during search. Recombination cuts allow 0.5% deviation; local moves allow 2% (2.1% in block refinement). These are temporary search limits; they are **not** the final population criterion.
5. Finish with whole-block population transfers and swaps, independently validate, and publish only maps satisfying the final constraints. Optional block-level partisan refinement is available in the scripts; the released sweep uses the balanced coarse-search result. This finite compute budget is not a convergence certificate.

Early exploratory warm-up used a sum of per-election exponential penalties before the weakest-election objective was adopted. The public replay starts from supplied checkpoints and never pretends that a changed objective reproduces those earlier bytes. The historical search used 600 recombination rounds × 5,000 attempts (seed 8000), plus local refinement within each round. The 2024 branch used 300 × 6,000 (seed 12000), beginning from the included coarse checkpoint. All checkpoint provenance and replay boundaries are stated in [reproduction instructions](REPRODUCE.md).

## Exact population finishing

The finishing algorithm removes a pool of boundary blocks while preserving a connected fixed core in every district. Each removed block keeps a direct connection to its original core. A block can move only to another fixed core it touches. Thus any chosen subset of these moves remains contiguous.

A bidirectional subset-sum dynamic program finds an exact net population transfer between adjacent districts, allowing simultaneous opposite-direction swaps. Surpluses are routed toward deficits. When needed, seeded zero-population boundary moves expose more transfer options; each also preserves connectivity. The algorithm seeks a feasible integer balance, not a partisan optimum. It exits unsuccessfully if no exact balance is found within its finite budget. Both published experimental maps pass an independent full-assignment check after finishing.

Finishing patches include population-balancing changes and label normalization. Applying them to the included unbalanced checkpoints exactly reconstructs the released block assignments. Reruns may choose another feasible solution on a different numerical stack; the patches preserve the exact published result.

## Independent validation and display

[`validate.py`](../scripts/validate.py) checks unique/full coverage, district labels, population conservation, the one-person maximum gap, all 26 connected cores, unchanged island exceptions and vote conservation. [`verify_release.py`](../scripts/verify_release.py) recomputes every district's results from the compact full model bundle, compares the published summaries, replays the checkpoints and checks artifact hashes. It verifies the 2024 sweep specifically. The historical all-election sweep is a separate reported outcome, not silently inferred from 2024 success.

District display boundaries are unions of assigned source blocks, simplified at 0.00065 degrees with topology preservation per polygon. The voting-unit overlay uses 0.0008 degrees. Independent simplification can create small display seams; these geometries never determine adjacency or population. Full block-assignment downloads and original Census polygons are the analytical authority.

The slider adds the same percentage-point shift to Democratic **two-party vote share** in every district, clipped to 0–100%. A one-point share shift changes margin by two points. It does not model turnout, incumbency or candidate quality. Historical bars and exported raw counts do not change with the slider.

The experiment imposes only its disclosed population and contiguity constraints. It does not optimize compactness or preserve municipalities, counties or communities of interest, and it does not evaluate the full set of legal requirements for adopting a congressional map.
