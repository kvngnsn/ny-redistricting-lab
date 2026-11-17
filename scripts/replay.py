"""Restore the published analytical state from the compact research bundle."""
import argparse,csv,shutil,gzip
import numpy as np
from scipy.sparse import coo_matrix,save_npz
from common import ROOT,CACHE

def main():
    args=argparse.ArgumentParser();args.add_argument('--unbalanced',action='store_true');opt=args.parse_args()
    b=np.load(ROOT/'research/model-inputs.npz',allow_pickle=False)
    np.savez_compressed(CACHE/'blocks.npz',**{k:b[k] for k in ['ids','pop','baseline','vtd','xy']})
    np.save(CACHE/'votes.npy',b['votes']);np.save(CACHE/'edges.npy',b['edges'])
    edges=b['edges'];graph=coo_matrix((np.ones(2*len(edges),np.int8),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(b['ids']),len(b['ids']))).tocsr();save_npz(CACHE/'graph.npz',graph)
    for filename in ['elections.json','coarse.npz','coarse-graph.npz']:
        shutil.copyfile(ROOT/'research'/filename,CACHE/filename)
    for name,source in [('candidate','sweep'),('stress','stress'),('statewide','statewide')]:
        if not (ROOT/f'research/checkpoints/{source}-before-balance.npy').exists():continue
        a=np.load(ROOT/f'research/checkpoints/{source}-before-balance.npy')
        if not opt.unbalanced:
            with gzip.open(ROOT/f'research/checkpoints/{name}-finish.csv.gz','rt') as f:
                for row in csv.DictReader(f):a[int(row['block_index'])]=int(row['district_zero_based'])
        np.save(CACHE/f'{name}.npy',a)
    shutil.copyfile(ROOT/'research/checkpoints/sweep-search-start.npy',CACHE/'sweep-search-start.npy')
    print('Restored', 'pre-balance checkpoints' if opt.unbalanced else 'published plans', 'and analytical inputs in .cache/')
if __name__=='__main__':main()
