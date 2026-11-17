"""Build the exact Census-block graph. No invented edges or nearest-neighbor links."""
import json
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
import shapely
from scipy.sparse import coo_matrix, save_npz
from scipy.sparse.csgraph import connected_components
from common import CACHE, PUBLIC, fetch, write_json

def main():
    blocks = fetch('blocks.zip', 'https://www2.census.gov/geo/tiger/TIGER2020/TABBLOCK20/tl_2020_36_tabblock20.zip')
    baseline = fetch('baseline.dbf', 'https://latfor.state.ny.us/maps/2024_Congress/CON24_Feb_28_2024.dbf')
    baf = fetch('block-vtd-crosswalk.zip', 'https://www2.census.gov/geo/docs/maps-data/data/baf2020/BlockAssign_ST36_NY.zip')
    vtd = fetch('vtd.zip', 'https://www2.census.gov/geo/tiger/TIGER2020PL/STATE/36_NEW_YORK/36/tl_2020_36_vtd20.zip')
    print('Reading Census polygons', flush=True)
    g = pyogrio.read_dataframe(blocks, columns=['GEOID20', 'POP20', 'ALAND20', 'AWATER20', 'COUNTYFP20', 'INTPTLAT20', 'INTPTLON20'])
    g = g.sort_values('GEOID20').reset_index(drop=True)
    assert len(g) == 288819 and g.GEOID20.is_unique
    assert int(g.POP20.sum()) == 20201249
    assert g.geometry.is_valid.all()
    assignment = pyogrio.read_dataframe(baseline, read_geometry=False).set_index('BLOCK')
    g['district'] = assignment.loc[g.GEOID20, 'DISTRICT'].to_numpy().astype('int16') - 1
    with zipfile.ZipFile(baf) as archive:
        crosswalk = pd.read_csv(archive.open('BlockAssign_ST36_NY_VTD.txt'), sep='|', dtype=str)
    print('BAF fields', list(crosswalk.columns), flush=True)
    crosswalk['vtd'] = crosswalk['BLOCKID'].str[:5] + crosswalk['DISTRICT']
    g['vtd'] = crosswalk.set_index('BLOCKID').loc[g.GEOID20, 'vtd'].to_numpy()
    g.to_pickle(CACHE / 'blocks.pkl')
    v = pyogrio.read_dataframe(vtd).sort_values('GEOID20').reset_index(drop=True)
    v.to_pickle(CACHE / 'vtd.pkl')
    np.savez_compressed(CACHE / 'blocks.npz', ids=g.GEOID20.to_numpy(dtype='U15'), pop=g.POP20.to_numpy(dtype=np.int64), baseline=g.district.to_numpy(dtype=np.int16), vtd=g.vtd.to_numpy(dtype='U11'), xy=np.column_stack([g.INTPTLON20.astype(float), g.INTPTLAT20.astype(float)]))
    print('Computing exact shared-boundary adjacency', flush=True)
    geom = g.geometry.to_numpy()
    tree = shapely.STRtree(geom)
    edges = []
    for start in range(0, len(g), 10000):
        a, b = tree.query(geom[start:start+10000], predicate='intersects')
        a += start
        keep = a < b
        a, b = a[keep], b[keep]
        # F***1****: disjoint interiors, one-dimensional boundary intersection.
        keep = shapely.relate_pattern(geom[a], geom[b], 'F***1****')
        edges.append(np.column_stack([a[keep], b[keep]]))
        if start % 50000 == 0:
            print('Graph', start, '/', len(g), flush=True)
    edges = np.concatenate(edges).astype(np.int32)
    graph = coo_matrix((np.ones(len(edges)*2, dtype=np.int8), (np.r_[edges[:,0], edges[:,1]], np.r_[edges[:,1], edges[:,0]])), shape=(len(g),len(g))).tocsr()
    save_npz(CACHE / 'graph.npz', graph)
    np.save(CACHE / 'edges.npy', edges)
    ncomp, labels = connected_components(graph, directed=False)
    report = {'blocks':len(g), 'population':int(g.POP20.sum()), 'edges':len(edges), 'graph_components':int(ncomp), 'component_sizes':np.bincount(labels).tolist(), 'component_populations':np.bincount(labels, weights=g.POP20).astype(int).tolist(), 'baseline':[]}
    for d in range(26):
        mask = g.district.to_numpy() == d
        nc, _ = connected_components(graph[mask][:,mask], directed=False)
        report['baseline'].append({'district':d+1,'population':int(g.POP20[mask].sum()),'components':int(nc)})
    write_json(CACHE / 'geometry-audit.json', report)
    print(json.dumps(report), flush=True)

if __name__ == '__main__':
    main()
