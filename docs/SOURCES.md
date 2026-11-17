# Sources and attribution

[Project overview](../README.md) · [Data licenses](DATA-LICENSES.md) · [Methodology](METHODOLOGY.md)

The election panel covers **13 statewide contests, 2008–2024**, on a common 2020 Census block geography. Historical values originate in 14,191 DRA VTD records; 2024 values originate in 12,984 New York precinct features. These are counts from the downloaded files, not claims that every historical ballot is geographically located. Source inspection date: November 16, 2026.

| Material | Source and public credit | Use in this project |
| --- | --- | --- |
| 2020 blocks and population | [U.S. Census Bureau, TIGER/Line New York blocks](https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_36_tabblock20.zip) | Original block geometry and unadjusted `POP20`; source for population constraints and the shared-boundary graph. |
| 2020 VTD boundaries | [U.S. Census Bureau, New York VTD shapefile](https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/36_NEW_YORK/36/tl_2020_36_vtd20.zip) | Geography matching DRA's `GEOID20`. The uppercase `NEW_YORK` path is intentional. |
| 2024 adopted congressional plan | [New York Legislative Task Force on Demographic Research and Reapportionment (LATFOR)](https://latfor.state.ny.us/maps/?sec=2024_congress): [block assignments](https://latfor.state.ny.us/maps/2024_Congress/CON24_Feb_28_2024.dbf), [shapefile](https://latfor.state.ny.us/maps/2024_Congress/CON24_shapefile_Feb_28_2024.zip) | Official February 28, 2024 baseline assignment. |
| Historical election package | [Dave's Redistricting, New York v05 archive](https://raw.githubusercontent.com/dra2020/vtd_data/master/2020_VTD/NY/Election_Data_NY.v05.zip), packaged by Social Good Fund for Dave's Redistricting | 12 statewide contests below. Original [archive license](data-licenses/DRA-ELECTION-v05.txt). |
| 2024 president | [The New York Times, presidential precinct project](https://github.com/nytimes/presidential-precinct-map-2024); New York results and boundaries supplied by **Benjamin J. Rosenblatt** | [New York GeoJSON](https://int.nyt.com/newsgraphics/elections/map-data/2024/national/NY-precincts-with-results.geojson.gz). The source labels New York boundaries official. |

LATFOR explicitly directs congressional work to **unadjusted Census data**, rather than its amended prisoner-adjusted population file. This project follows that direction; its population measure is neither turnout nor citizen voting-age population. [LATFOR population guidance](https://latfor.state.ny.us/data/).

## Historical source chain

The attribution below is transcribed from the [v05 archive license](data-licenses/DRA-ELECTION-v05.txt); all historical values are DRA's harmonized VTD values rather than untouched county returns.

| Year | Included contests | Original contributor |
| --- | --- | --- |
| 2008 | President | Steve Gerontakis, with John Mifflin |
| 2012 | President | Ryne Rohla / Decision Desk HQ |
| 2016 | President; U.S. Senate | Voting and Election Science Team (VEST) |
| 2018 | U.S. Senate; governor; attorney general | VEST |
| 2020 | President | VEST |
| 2022 | U.S. Senate; governor; attorney general; comptroller | [Benjamin J. Rosenblatt](https://www.benjrosenblatt.com/new-york-2022-election-district-level-data), using county Boards of Elections results standardized with OpenElections |

DRA composites and congressional returns are excluded: the panel uses distinct statewide races so all districts are evaluated against the same ballot. [Archive contents and field definitions](https://github.com/dra2020/vtd_data/tree/master/2020_VTD/NY).

## What the numbers mean

**Block-level election values are estimates.** A source precinct/VTD can contain many Census blocks and can be split by a proposed district. Allocating its votes to blocks using population weights does not reveal how those blocks actually voted. Reaggregation preserves source totals where source units can be assigned; it does not remove ecological uncertainty. The implementation and any unassigned coverage belong in the [methodology](METHODOLOGY.md) and build audit.

Historical boundaries and votes have already been harmonized by DRA. DRA states that its source data may be aggregated or disaggregated. Later allocation onto blocks is a further modeling step, not additional observed information. [DRA archive license](data-licenses/DRA-ELECTION-v05.txt).

New York fusion votes must follow the **candidate**, including the candidate's minor-party lines. The official 2022 statewide candidates appear on Democratic/Working Families or Republican/Conservative lines; the 2024 presidential ticket does too. [2022 governor](https://results.elections.ny.gov/contest/1), [2024 president](https://results.elections.ny.gov/contest/5591).

The following audit compares statewide sums before this project's spatial allocation. The 2022 reference is Rosenblatt's April 3, 2024 workbook, with `DEM + WOR` and `REP + CON`; the 2024 reference is the state Board of Elections candidate totals. Differences are retained rather than silently rescaled.

| Contest | Imported D / R | Reference D / R | Imported minus reference D / R |
| --- | ---: | ---: | ---: |
| 2022 governor | 3,136,974 / 2,759,364 | 3,140,426 / 2,762,591 | −3,452 / −3,227 |
| 2022 comptroller | 3,301,406 / 2,460,550 | 3,305,103 / 2,463,409 | −3,697 / −2,859 |
| 2022 attorney general | 3,165,392 / 2,628,551 | 3,168,889 / 2,631,625 | −3,497 / −3,074 |
| 2022 U.S. Senate | 3,316,913 / 2,498,180 | 3,320,554 / 2,501,151 | −3,641 / −2,971 |
| 2024 president | 4,619,551 / 3,579,513 | 4,619,543 / 3,579,519 | +8 / −6 |

References: [2022 original workbook](https://irp.cdn-website.com/fa110e79/files/uploaded/NY_2022GE_ED_Updated040324.xlsx), [DRA v05](https://raw.githubusercontent.com/dra2020/vtd_data/master/2020_VTD/NY/Election_Data_NY.v05.zip), [2024 NYT file](https://int.nyt.com/newsgraphics/elections/map-data/2024/national/NY-precincts-with-results.geojson.gz), [2024 official results](https://results.elections.ny.gov/contest/5591). The 2022 official governor totals are 3,140,415 / 2,762,581, slightly different again from the updated county-based workbook. [Official governor results](https://results.elections.ny.gov/contest/1).

Rosenblatt identifies cumulative, federal and other nongeographic vote rows excluded from the precinct shapefile, and county updates that differ from statewide certification. These explain why exact source-version and coverage checks matter; this audit does not attribute every discrepancy to one cause. [2022 source notes](https://www.benjrosenblatt.com/new-york-2022-election-district-level-data).

NYT's national notes also describe omitted tiny/suppressed precincts, incomplete write-in reporting and some unmatched results. Its New York file is used as supplied; a close statewide match does not certify every precinct. [NYT caveats](https://github.com/nytimes/presidential-precinct-map-2024#general-caveats).

## Reproducible source fingerprints

| Download | SHA-256 |
| --- | --- |
| DRA `Election_Data_NY.v05.zip` | `ab18e6970eea1f7d227632f42da849dcac841ba69373a62676c5aa23d5b6b215` |
| NYT `NY-precincts-with-results.geojson.gz` | `1b653891e308cb325c419e3627b4841544506c7a499f13edd4f7959f5ba1ab53` |
| DRA `Election_Data_NY.v04.zip` (audited alternative, not the selected panel) | `0d9b51d3f3e4b181101cb18d8d2a4383ea2bf7c848635b268b53b0b8ec2c87ae` |

Downloads at mutable URLs may change. The hashes identify the inspected bytes; the build should fail or record a changed source rather than pretend the update is identical.

## Credits and exclusions

“2024 Precinct-Level Election Results.” *The New York Times*, accessed November 16, 2026. [Published map](https://www.nytimes.com/interactive/2025/us/elections/2024-election-map-precinct-results.html). See the preserved [NYT contributor credits](data-licenses/NYT-CREDITS.md), [Rosenblatt permission and contributor acknowledgments](data-licenses/BJR-PERMISSION.md), and [source license obligations](DATA-LICENSES.md).

This build does not import RDH-distributed election/CVAP files or DRA v07/v08 election panels. Those versions incorporate additional RDH restrictions; using independently supplied versions must not be mistaken for permission to substitute later downloads. [DRA v08 license](data-licenses/DRA-ELECTION.txt), [RDH terms](https://redistrictingdatahub.org/terms-and-conditions/).
