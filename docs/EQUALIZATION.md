# Matching the statewide margin

[Explorer](https://kvngnsn.github.io/ny-redistricting-lab/#plan=statewide&election=24_PRES) · [Original methodology](METHODOLOGY.md) · [Numerical result](../research/equalization/result.json)

The target is the **2024 statewide Democratic two-party margin: D+12.684838 points**. This extension optimizes proximity to that target in every district. It retains the original maps for comparison and keeps the same data, whole-block population model and two approved island exceptions.

## What changed

The original sweep search rewarded positive Democratic margins but did not directly penalize districts far above the statewide result. It left considerable vote concentration: its margins ranged from D+1.37 to D+62.54. The new search penalizes deviations **in both directions**.

For each district, let `e = district_margin − statewide_margin`, expressed as a fraction. The local objective is:

```
sum(e² + alpha × e⁴)
+ population_weight × sum(((population − ideal) / ideal)²)
```

The retained search configurations state `alpha`, seeds, annealing temperatures, attempted moves and temporary population tolerances. Larger fourth-power weights emphasize the most extreme districts. The final result is selected by the largest absolute margin error **after exact population finishing**, not by a favorable intermediate result that violates the constraints.

Several seeded chains start from the prior experiments. The search alternates connected boundary moves and two-district spanning-tree recombinations. A finer graph subdivides the original connected units into **59,010 connected groups**: a group generally contains at most 500 residents and 20 Census blocks; a single block over that population remains intact. The finer graph uses the same exact original adjacency, without invented edges. Optional zero-vote/zero-population move thinning reduces wasted computation; its probability is recorded in the configuration.

Exploratory chains may temporarily permit substantial population imbalance to allow larger geographic changes. Their annealing schedules tighten population constraints and increase the population penalty. These interim maps are not offered as valid plans. Every published experimental plan must pass the one-person maximum population-gap test and independent connectivity checks.

A second, joint-assignment heuristic removes movable boundary blocks while preserving connected district cores. A mixed-integer program then minimizes the largest absolute partisan surplus, normalized by each district's pre-move turnout, while limiting population changes. The partisan surplus of a block is `(D−R) − statewide_margin × (D+R)`. Every moved block must attach directly to an eligible fixed core. This normalization approximates the ratio objective; a proposed result is accepted only if its **recomputed actual maximum margin gap improves**. Time-limited solves are not optimality certificates.

## Reading the comparison

- **Target gap** colors districts by their margin minus the statewide margin for the selected election.
- **Largest gap from statewide** is the maximum absolute difference, in percentage points, across the 26 districts.
- The district inspector reports each district's signed difference; the list can sort by farthest from statewide.
- The objective uses 2024. The other 12 elections remain historical stress tests, each compared with its own statewide result.
- The result file records the complete final margins, maximum and RMS errors, comparison to the original sweep, retained stages and whether optimality was proved (**false**).

## Exact equality versus a close match

The supplied 2024 counts are **4,619,551 Democratic** and **3,579,513 Republican**, with greatest common divisor **1**. Exact equality of a district's ratio to the statewide ratio would require its D/R counts to be an integer multiple of that entire statewide pair. Therefore, 26 positive-vote districts cannot all have that exact ratio under these indivisible integer counts.

That arithmetic observation does **not** explain away a multi-point gap or prove that a much closer approximation is impossible. It only rules out literal equality to every decimal place. The remaining reported spread is a limitation of the finite search. No global optimum, impossibility bound for a close match, or electoral-safety guarantee is claimed.

Split-precinct values remain population-weighted estimates. Changing the optimization objective does not make those allocations observed votes or reduce their underlying uncertainty. [Sources and data terms](SOURCES.md).

## Replay and further search

The standard `scripts/replay.py` and `scripts/verify_release.py` include the new map. Its exact pre-balance assignment and finishing patch are in `research/checkpoints/`. The full graph and vote inputs are unchanged.

`research/equalization/` contains the selected experiment's configurations, saved starts, logs, refined graph, balancing record and result. These explicit starts define each stage's reproduction boundary; an early-stopped run retains its original scheduled annealing duration. Run `python scripts/reproduce_equalization.py --stage equal-polish` to replay the final retained stage with its saved start and recorded parameters. The wrapper also supports the other retained stages and respects early-stop boundaries without changing their original annealing schedules. The `--rounds` value controls the temperature schedule, so changing it changes the experiment.

`publish_equalization.py` independently validates a selected balanced assignment, matches district labels to the reference by population overlap, preserves the approved island assignments, and creates replay artifacts. `export_site.py --reuse-geometry` reuses display geometry only when the old and current full assignments are equal. Release hashes and all district results are verified before deployment.
