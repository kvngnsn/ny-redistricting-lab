# Data licenses

[Project overview](../README.md) · [Source attribution](SOURCES.md)

**The project code and the data have separate licenses.** The repository's MIT license covers original software and documentation, subject to credited third-party material. It does not relicense source datasets, source notices, or data derived from them.

| Material | Applicable terms | Required handling |
| --- | --- | --- |
| Original project code | [MIT](../LICENSE) | Retain the project copyright and license notice. |
| Census TIGER/Line geography | U.S. government public-domain geographic data. [Census statement](https://www.census.gov/newsroom/archives/2014-pr/cb14-208.html) | Credit the U.S. Census Bureau; identify project modifications. Do not suggest Census endorsement. |
| LATFOR baseline assignments | Official [public assignment release](https://latfor.state.ny.us/maps/?sec=2024_congress) | Preserve source/date attribution. The project does not claim ownership of or apply MIT to the source table. |
| DRA v05 historical election values and adaptations | [Original archive license](data-licenses/DRA-ELECTION-v05.txt): CC BY-SA 4.0, plus the archive's explicit prohibition on selling data, and any original-source restrictions | Credit DRA and each original contributor; retain notices, mark transformations, preserve applicable ShareAlike terms, and do not sell the data. This is not a blanket permissive open-data license. |
| VEST values inside the selected DRA archive | The archive explicitly identifies [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) for VEST, in addition to DRA packaging terms | Credit VEST and DRA. Keep the archived version and its notice; do not assume another release has identical terms. |
| Rosenblatt 2022 values inside DRA v05 | [Author's public permission and acknowledgments](data-licenses/BJR-PERMISSION.md), plus DRA packaging terms | Credit Benjamin J. Rosenblatt and link his source page; retain contributor acknowledgments. |
| NYT 2024 data and adaptations | [NYT Computational Use of Data Agreement v1.0 – Non-Commercial](data-licenses/NYT-C-UDA.txt) | Computational use; noncommercial redistribution; retain all attribution; bind downstream recipients to C-UDA. Public results must credit NYT and remain noncommercial, except permitted journalistic editorial uses. |

The data-bearing downloads and mixed-source outputs retain the restrictions applicable to each component. **Redistributing this repository does not make its election data MIT.** Keep historical and 2024 source notices with exports; do not remove them when combining or reaggregating data. The NYT agreement distinguishes redistributed data from computational results, and both have explicit conditions. [NYT agreement, sections 2–3 and 5](data-licenses/NYT-C-UDA.txt).

## Notices preserved verbatim

- [DRA v05 election license](data-licenses/DRA-ELECTION-v05.txt): selected historical panel, created April 21, 2024.
- [NYT C-UDA](data-licenses/NYT-C-UDA.txt) and [received attribution](data-licenses/NYT-CREDITS.md): selected 2024 panel.
- [DRA v04 election license](data-licenses/DRA-ELECTION-v04.txt): audited 2016–2020 alternative.
- [DRA v08 election license](data-licenses/DRA-ELECTION.txt) and [demographic license](data-licenses/DRA-DEMOGRAPHIC.txt): retained audit records for versions not used in the selected election/population panel.

## Why some public files are excluded

The DRA v07/v08 New York election licenses identify RDH for 2022 and 2024 and incorporate RDH's terms. RDH's terms restrict use to noncommercial, nonpartisan purposes and prohibit use to favor a political party through redistricting. Those downloads are not suitable for the experiment's stated objective. The selected 2022 archive instead identifies Rosenblatt directly and links to his own permission; 2024 is independently provided by NYT under C-UDA. [Inspected v08 license](data-licenses/DRA-ELECTION.txt), [RDH terms](https://redistrictingdatahub.org/terms-and-conditions/), [selected v05 license](data-licenses/DRA-ELECTION-v05.txt), [NYT agreement](data-licenses/NYT-C-UDA.txt).

The unused DRA demographic archive separately credits RDH for disaggregated CVAP. The project uses direct Census `POP20`, not that CVAP product. [Demographic notice](data-licenses/DRA-DEMOGRAPHIC.txt).

These notes identify the terms supplied with the inspected releases and the project's source choices. Replacing a release, adding data, commercializing outputs, or changing redistribution terms requires checking the relevant source license again.
