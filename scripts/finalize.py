"""Label plans by maximum population overlap, validate, and package replay inputs."""
import json,csv,shutil,gzip
import numpy as np
from scipy.sparse import load_npz
from scipy.optimize import linear_sum_assignment
from common import CACHE,ROOT,write_json
from validate import validate,ISLAND_EXCEPTIONS

def main():
    b=np.load(CACHE/'blocks.npz');votes=np.load(CACHE/'votes.npy');g=load_npz(CACHE/'graph.npz')
    archive=dict(b);archive.update(votes=votes,edges=np.load(CACHE/'edges.npy'),nyt_precinct=np.load(CACHE/'nyt-precinct-assignments.npy'))
    np.savez_compressed(ROOT/'research/model-inputs.npz',**archive)
    for source,name in [('sweep','candidate'),('stress','stress')]:
        original=np.load(ROOT/f'research/checkpoints/{source}-before-balance.npy')
        a=np.load(CACHE/f'{source}.npy');overlap=np.zeros((26,26),np.int64)
        np.add.at(overlap,(a,b['baseline']),b['pop'])
        old,new=linear_sum_assignment(-overlap);mapping=np.empty(26,np.int16);mapping[old]=new
        a=mapping[a];a[np.isin(b['ids'],ISLAND_EXCEPTIONS)]=b['baseline'][np.isin(b['ids'],ISLAND_EXCEPTIONS)]
        report=validate(a,b,votes,g)
        assert report['constraints_pass'],f'{name} failed final constraints'
        if name=='candidate':assert all(d['votes'][-1][0]>d['votes'][-1][1] for d in report['districts'])
        np.save(CACHE/f'{name}.npy',a)
        # Record both population-balancing changes and pure label normalization for exact replay.
        with gzip.open(ROOT/f'research/checkpoints/{name}-finish.csv.gz','wt',newline='') as f:
            w=csv.writer(f);w.writerow(['block_index','district_zero_based']);w.writerows((int(i),int(a[i])) for i in np.flatnonzero(a!=original))
        print(name,'exact',report['population_range'],'connected',report['connected_districts'],'robust',report['robust_democratic_districts'])
    shutil.copyfile(CACHE/'downloads.json',ROOT/'research/sources.lock.json')
    for f in ['elections.json','coarse.npz','coarse-graph.npz']:
        shutil.copyfile(CACHE/f,ROOT/'research'/f)
if __name__=='__main__':main()
