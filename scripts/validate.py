"""Independent full-assignment validation. Display simplifications are never inputs."""
import argparse
import json
import gzip
import csv
import numpy as np
from scipy.sparse import load_npz
from scipy.sparse.csgraph import connected_components
from common import CACHE, PUBLIC, write_json

ISLAND_EXCEPTIONS = ['360610001001000','360610001001001']

def validate(assignment, block, votes, graph):
    assert len(assignment)==len(block['ids']), 'Assignment must cover every block'
    assert np.all((assignment>=0)&(assignment<26)), 'Invalid district label'
    assert len(np.unique(block['ids']))==len(assignment), 'Duplicate Census block IDs'
    exceptions=np.isin(block['ids'],ISLAND_EXCEPTIONS)
    assert int(block['pop'][exceptions].sum())==0
    assert np.array_equal(assignment[exceptions],block['baseline'][exceptions]),'Island assignments changed'
    districts=[];total_votes=np.zeros(votes.shape[1:],dtype=np.int64)
    for d in range(26):
        full=assignment==d
        mask=full&~exceptions
        nodes=np.flatnonzero(mask)
        ncomp=connected_components(graph[nodes][:,nodes],directed=False,return_labels=False) if len(nodes) else 0
        sums=votes[full].sum(axis=0);total_votes+=sums
        denominator=sums[:,:2].sum(axis=1)
        margins=np.divide(sums[:,0]-sums[:,1],denominator,out=np.full(len(sums),np.nan),where=denominator>0)
        districts.append({'id':d+1,'population':int(block['pop'][full].sum()),'blocks':int(full.sum()),'components':int(ncomp),'island_exceptions':int((full&exceptions).sum()),'votes':sums.tolist(),'minimum_margin':float(np.nanmin(margins))})
    pops=[d['population'] for d in districts]
    result={'complete':True,'blocks':len(assignment),'population_conserved':sum(pops)==20201249,'population':sum(pops),'population_min':min(pops),'population_max':max(pops),'population_range':max(pops)-min(pops),'population_equal':max(pops)-min(pops)<=1,'connected_districts':sum(d['components']==1 for d in districts),'island_exceptions':ISLAND_EXCEPTIONS,'strict_geographic_contiguity_without_exceptions':False,'votes_conserved':bool(np.array_equal(total_votes,votes.sum(axis=0))),'robust_democratic_districts':sum(d['minimum_margin']>0 for d in districts),'minimum_margin':min(d['minimum_margin'] for d in districts),'districts':districts}
    result['constraints_pass']=result['complete'] and result['population_conserved'] and result['population_equal'] and result['connected_districts']==26 and result['votes_conserved']
    result['all_elections_sweep_achieved']=result['constraints_pass'] and result['robust_democratic_districts']==26
    result['democratic_leads_by_election']=[sum(d['votes'][e][0]>d['votes'][e][1] for d in districts) for e in range(votes.shape[1])]
    result['sweeps_by_election']=[result['constraints_pass'] and count==26 for count in result['democratic_leads_by_election']]
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--require-constraints',action='store_true');args=p.parse_args()
    b=np.load(CACHE/'blocks.npz');v=np.load(CACHE/'votes.npy');g=load_npz(CACHE/'graph.npz')
    results={name:validate(a,b,v,g) for name,a in [('reference',b['baseline']),('candidate',np.load(CACHE/'candidate.npy')),('stress',np.load(CACHE/'stress.npy'))]}
    if (CACHE/'statewide.npy').exists():results['statewide']=validate(np.load(CACHE/'statewide.npy'),b,v,g)
    write_json(PUBLIC/'validation.json',results)
    for name,r in results.items():print(name,json.dumps({k:v for k,v in r.items() if k!='districts'}))
    if args.require_constraints and not all(results[p]['constraints_pass'] for p in results if p!='reference'):raise SystemExit('Candidate failed hard constraints')

if __name__=='__main__':main()
