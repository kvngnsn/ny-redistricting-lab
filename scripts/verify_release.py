"""Verify every published plan against full-resolution model inputs, offline."""
import csv,gzip,json,hashlib
import numpy as np
from scipy.sparse import coo_matrix
from common import ROOT,PUBLIC
from validate import validate

def main():
    inputs=np.load(ROOT/'research/model-inputs.npz',allow_pickle=False)
    edges=inputs['edges'];n=len(inputs['ids'])
    graph=coo_matrix((np.ones(2*len(edges),np.int8),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(n,n)).tocsr()
    summary=json.loads((PUBLIC/'summary.json').read_text());audits=json.loads((PUBLIC/'validation.json').read_text())
    assert np.array_equal(inputs['votes'].sum(axis=0),[e['source_totals'] for e in summary['elections']])
    for plan in summary['plans']:
        with gzip.open(PUBLIC/plan['assignments'],'rt') as f:rows=list(csv.DictReader(f))
        assert [r['GEOID20'] for r in rows]==inputs['ids'].tolist()
        assignment=np.array([int(r['district'])-1 for r in rows],np.int16)
        actual=validate(assignment,inputs,inputs['votes'],graph)
        for k,v in actual.items():
            if k=='districts':continue
            assert v==audits[plan['id']][k],f"Audit mismatch {plan['id']} {k}"
        for d,published in zip(actual['districts'],plan['districts']):
            assert all(d[k]==published[k] for k in d),f"District mismatch {plan['id']} {d['id']}"
        if plan['id']!='reference':
            assert actual['constraints_pass']
            source='sweep' if plan['id']=='candidate' else 'stress'
            replay=np.load(ROOT/f'research/checkpoints/{source}-before-balance.npy')
            with gzip.open(ROOT/f"research/checkpoints/{plan['id']}-finish.csv.gz",'rt') as f:
                for row in csv.DictReader(f):replay[int(row['block_index'])]=int(row['district_zero_based'])
            assert np.array_equal(replay,assignment),'Checkpoint replay mismatch'
        else:assert np.array_equal(assignment,inputs['baseline'])
        if plan['id']=='candidate':assert all(d['votes'][-1][0]>d['votes'][-1][1] for d in actual['districts'])
        print(plan['id'],':',actual['blocks'],'blocks;',actual['population_range'],'person range;',actual['connected_districts'],'connected; all election totals conserved')
    manifest=json.loads((ROOT/'research/release-hashes.json').read_text())
    for name,expected in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,f'Changed release artifact: {name}'
    print('Release hashes and exact checkpoint replay verified.')
if __name__=='__main__':main()
