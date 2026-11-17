"""Allocate licensed historical VTD and 2024 precinct counts to Census blocks.

These are modeled block votes, never observations of individual/block ballots.
Each source unit's D/R/other totals are conserved by largest-remainder rounding.
"""
import gzip
import io
import json
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
import shapely
from common import CACHE, PUBLIC, fetch, write_json

HISTORICAL = [
    ('08_PRES', '2008 president'), ('12_PRES', '2012 president'),
    ('16_PRES', '2016 president'), ('16_SEN', '2016 Senate'),
    ('18_SEN', '2018 Senate'), ('18_GOV', '2018 governor'), ('18_AG', '2018 attorney general'),
    ('20_PRES', '2020 president'), ('22_SEN', '2022 Senate'), ('22_GOV', '2022 governor'),
    ('22_AG', '2022 attorney general'), ('22_CMPTR', '2022 comptroller'),
]

def allocate(group, totals, pop, area):
    """Largest remainder with stable block-index ties; preserve every source total."""
    output = np.zeros((len(group), totals.shape[1]), dtype=np.int64)
    order = np.argsort(group, kind='stable')
    sorted_groups = group[order]
    starts = np.r_[0, np.flatnonzero(np.diff(sorted_groups)) + 1, len(order)]
    missing = []
    seen = set()
    for start, end in zip(starts[:-1], starts[1:]):
        idx = order[start:end]
        gid = int(group[idx[0]])
        if gid < 0:
            continue
        seen.add(gid)
        weights = pop[idx].astype(float)
        if weights.sum() == 0:
            weights = np.maximum(area[idx], 1).astype(float)
        weights /= weights.sum()
        expected = weights[:, None] * totals[gid][None, :]
        rounded = np.floor(expected).astype(np.int64)
        remaining = totals[gid] - rounded.sum(axis=0)
        for col, remainder in enumerate(remaining):
            priority = np.argsort(-(expected[:, col] - rounded[:, col]), kind='stable')
            rounded[priority[:int(remainder)], col] += 1
        output[idx] = rounded
    for gid in range(len(totals)):
        if gid not in seen and totals[gid].sum() > 0:
            missing.append({'source_unit':gid,'unallocated_counts':totals[gid].tolist()})
    return output, missing

def main():
    b = pd.read_pickle(CACHE / 'blocks.pkl')
    pop = b.POP20.to_numpy(dtype=np.int64)
    area = b.ALAND20.to_numpy(dtype=float)
    historical = fetch('historical-v05.zip', 'https://raw.githubusercontent.com/dra2020/vtd_data/master/2020_VTD/NY/Election_Data_NY.v05.zip')
    with zipfile.ZipFile(historical) as z:
        hist = pd.read_csv(z.open('election_data_NY.v05.csv'), dtype={'GEOID20':str})
    hidx = {v:i for i,v in enumerate(hist.GEOID20)}
    group = np.array([hidx.get(v, -1) for v in b.vtd], dtype=np.int32)
    audits = []
    elections = []
    votes = []
    for key, label in HISTORICAL:
        prefix = 'E_' + key
        d = hist[prefix + '_Dem'].to_numpy(np.int64)
        r = hist[prefix + '_Rep'].to_numpy(np.int64)
        total = hist[prefix + '_Total'].to_numpy(np.int64)
        assert np.all(total >= d+r)
        source = np.column_stack([d,r,total-d-r])
        allocated, missing = allocate(group, source, pop, area)
        if missing:
            raise ValueError(f'Unallocated historical votes {key}: {missing[:3]}')
        assert np.array_equal(allocated.sum(axis=0), source.sum(axis=0))
        votes.append(allocated)
        elections.append({'id':key, 'label':label,'year':2000+int(key[:2]),'source':'DRA v05 / credited original providers','geography':'2020 Census VTD','allocation':'Population-weighted block estimates; largest remainder','source_totals':source.sum(axis=0).tolist()})
        print(label, source.sum(axis=0).tolist(), flush=True)
    nyt = fetch('nyt-2024-ny.geojson.gz','https://int.nyt.com/newsgraphics/elections/map-data/2024/national/NY-precincts-with-results.geojson.gz')
    print('Reading 2024 precincts', flush=True)
    with gzip.open(nyt,'rt') as f:
        features = json.load(f)['features']
    p = gpd.GeoDataFrame.from_features(features, crs=4326)
    p.geometry = p.geometry.make_valid()
    # Census internal points preserve exact source associations when inside a precinct.
    # Remaining blocks use their greatest-area polygon overlap, not an invented neighbor.
    geom = p.geometry.to_numpy()
    tree = shapely.STRtree(geom)
    points = shapely.points(b.INTPTLON20.astype(float), b.INTPTLAT20.astype(float))
    aa, bb = tree.query(points, predicate='intersects')
    groups = np.full(len(b), -1, dtype=np.int32)
    groups[aa] = bb
    unresolved = np.flatnonzero(groups < 0)
    bg = b.geometry.to_numpy()
    for i in unresolved:
        js = tree.query(bg[i], predicate='intersects')
        if len(js):
            overlap = shapely.area(shapely.intersection(bg[i], geom[js]))
            if overlap.max() > 0:
                groups[i] = js[np.argmax(overlap)]
    # If a very small source precinct contains no Census internal point, assign the
    # overlapping block with greatest area ONLY if it doesn't orphan another source.
    counts = np.bincount(groups[groups >= 0], minlength=len(p))
    bt = shapely.STRtree(bg)
    for source in np.flatnonzero(counts == 0):
        js = bt.query(geom[source], predicate='intersects')
        if not len(js):
            continue
        overlap = shapely.area(shapely.intersection(geom[source], bg[js]))
        for j in np.argsort(-overlap):
            block = js[j]
            old = groups[block]
            if overlap[j] > 0 and (old < 0 or counts[old] > 1):
                if old >= 0: counts[old] -= 1
                groups[block] = source
                counts[source] += 1
                break
    d = p.votes_dem.fillna(0).to_numpy(np.int64)
    r = p.votes_rep.fillna(0).to_numpy(np.int64)
    total = p.votes_total.fillna(0).to_numpy(np.int64)
    assert np.all(total >= d+r)
    source = np.column_stack([d,r,total-d-r])
    allocated, missing = allocate(groups, source, pop, area)
    audit = {'source_precincts':len(p),'assigned_blocks':int((groups>=0).sum()), 'unassigned_blocks':int((groups<0).sum()),'unassigned_2020_population':int(pop[groups<0].sum()),'unallocated_precincts':missing,'source_totals':source.sum(axis=0).tolist(),'allocated_totals':allocated.sum(axis=0).tolist(),'official_boundary_true':int(p.official_boundary.fillna(False).astype(bool).sum())}
    write_json(CACHE / 'nyt-allocation-audit.json', audit)
    print('2024 allocation audit',json.dumps(audit),flush=True)
    if missing:
        raise ValueError('Unallocated 2024 precincts; inspect audit before proceeding')
    assert np.array_equal(allocated.sum(axis=0), source.sum(axis=0))
    votes.append(allocated)
    elections.append({'id':'24_PRES','label':'2024 president','year':2024,'source':'The New York Times / Benjamin J. Rosenblatt','geography':'2024 election precincts','allocation':'Census internal point, then greatest overlap; population-weighted block estimates','source_totals':source.sum(axis=0).tolist()})
    np.save(CACHE/'votes.npy', np.stack(votes, axis=1))
    np.save(CACHE/'nyt-precinct-assignments.npy',groups)
    p.to_pickle(CACHE/'nyt-precincts.pkl')
    write_json(CACHE/'elections.json',elections)

if __name__ == '__main__':
    main()
