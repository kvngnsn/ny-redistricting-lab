"""Reproducible connected-unit simulated annealing; no optimality claim.

Search uses connected intersections of VTDs with the reference plan, then whole
Census blocks. Exact population is a separately audited finishing constraint.
"""
import argparse
import json
import time
import numpy as np
from numba import njit
from scipy.sparse import coo_matrix, load_npz, save_npz
from scipy.sparse.csgraph import connected_components
from common import CACHE, write_json

@njit(cache=True)
def donor_connected(node, donor, assignment, indptr, indices, visited, stamp, queue):
    wanted = 0
    start = -1
    for k in range(indptr[node],indptr[node+1]):
        j = indices[k]
        if assignment[j] == donor:
            wanted += 1
            start = j
    if wanted <= 1:
        return True
    visited[node] = stamp
    visited[start] = stamp
    queue[0] = start
    head, tail, found = 0, 1, 0
    while head < tail:
        u = queue[head]
        head += 1
        for k in range(indptr[node],indptr[node+1]):
            if indices[k] == u:
                found += 1
                break
        if found == wanted:
            return True
        for k in range(indptr[u],indptr[u+1]):
            w = indices[k]
            if assignment[w] == donor and visited[w] != stamp:
                visited[w] = stamp
                queue[tail] = w
                tail += 1
    return False

@njit(cache=True)
def partisan_cost(counts):
    # The weakest observed scenario controls a district's cost. Correlated strong
    # elections cannot hide a loss in a difficult election through averaging.
    worst = 1.0
    for e in range(counts.shape[0]):
        d, r = counts[e,0], counts[e,1]
        margin = (d-r) / max(d+r,1.0)
        worst = min(worst,margin)
    return np.exp(-25.0 * worst)

@njit(cache=True)
def anneal(assignment,pop,votes,indptr,indices,edges,attempts,seed,temperature,pop_weight,slack):
    np.random.seed(seed)
    n = len(assignment)
    ne = votes.shape[1]
    total_pop = pop.sum()
    target = total_pop / 26.0
    dp = np.zeros(26,dtype=np.int64)
    dv = np.zeros((26,ne,3),dtype=np.float64)
    for i in range(n):
        dp[assignment[i]] += pop[i]
        dv[assignment[i]] += votes[i]
    dc = np.zeros(26)
    for d in range(26):
        dc[d] = partisan_cost(dv[d])
    visited = np.zeros(n,dtype=np.int64)
    queue = np.empty(n,dtype=np.int32)
    accepted = 0
    for step in range(attempts):
        edge = edges[np.random.randint(len(edges))]
        i, j = edge[0],edge[1]
        if np.random.random() < .5:
            i,j = j,i
        a,b = assignment[i],assignment[j]
        if a == b:
            continue
        pa,pb = dp[a]-pop[i],dp[b]+pop[i]
        if pa < target*(1-slack) or pb > target*(1+slack):
            continue
        va,vb = dv[a]-votes[i],dv[b]+votes[i]
        ca,cb = partisan_cost(va),partisan_cost(vb)
        before_pop = ((dp[a]-target)/target)**2 + ((dp[b]-target)/target)**2
        after_pop = ((pa-target)/target)**2 + ((pb-target)/target)**2
        delta = ca+cb-dc[a]-dc[b]+pop_weight*(after_pop-before_pop)
        if delta > 0 and np.random.random() >= np.exp(-delta/max(temperature,1e-12)):
            continue
        if not donor_connected(i,a,assignment,indptr,indices,visited,step+1,queue):
            continue
        assignment[i] = b
        dp[a],dp[b] = pa,pb
        dv[a],dv[b] = va,vb
        dc[a],dc[b] = ca,cb
        accepted += 1
    return assignment, accepted, dp, dv, dc.sum()

def coarsen():
    block = np.load(CACHE/'blocks.npz')
    edges = np.load(CACHE/'edges.npy')
    votes = np.load(CACHE/'votes.npy')
    key = np.char.add(block['vtd'], block['baseline'].astype(str))
    keep = key[edges[:,0]] == key[edges[:,1]]
    e = edges[keep]
    graph = coo_matrix((np.ones(len(e)*2,dtype=np.int8),(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(len(key),len(key))).tocsr()
    count, groups = connected_components(graph,directed=False)
    pop = np.bincount(groups,weights=block['pop']).astype(np.int64)
    cv = np.zeros((count,votes.shape[1],3),dtype=np.int64)
    np.add.at(cv,groups,votes)
    assignment = np.zeros(count,dtype=np.int16)
    assignment[groups] = block['baseline']
    ce = np.sort(groups[edges],axis=1)
    ce = np.unique(ce[ce[:,0]!=ce[:,1]],axis=0).astype(np.int32)
    cg = coo_matrix((np.ones(len(ce)*2,dtype=np.int8),(np.r_[ce[:,0],ce[:,1]],np.r_[ce[:,1],ce[:,0]])),shape=(count,count)).tocsr()
    np.savez_compressed(CACHE/'coarse.npz',pop=pop,votes=cv,assignment=assignment,groups=groups,edges=ce)
    save_npz(CACHE/'coarse-graph.npz',cg)
    print('Connected search units',count,'edges',len(ce),flush=True)

def stats(dp,dv,cost):
    margin = (dv[:,:,0]-dv[:,:,1])/np.maximum(1,dv[:,:,:2].sum(axis=2))
    return {'cost':float(cost),'robust_democratic_districts':int((margin.min(axis=1)>0).sum()),'minimum_margin':float(margin.min()),'democratic_districts_by_election':(margin>0).sum(axis=0).tolist(),'population_range':int(dp.max()-dp.min()),'populations':dp.tolist()}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--epochs',type=int,default=25)
    p.add_argument('--attempts',type=int,default=2000000)
    p.add_argument('--seed',type=int,default=2601)
    p.add_argument('--resume',action='store_true')
    p.add_argument('--blocks',action='store_true')
    p.add_argument('--election',default='all')
    p.add_argument('--suffix',default='candidate')
    p.add_argument('--population-weight',type=float,default=10000.)
    args=p.parse_args()
    if not (CACHE/'coarse.npz').exists(): coarsen()
    c=np.load(CACHE/'coarse.npz')
    if args.blocks:
        d=np.load(CACHE/'blocks.npz');pop=d['pop'];votes=np.load(CACHE/'votes.npy');edges=np.load(CACHE/'edges.npy');graph=load_npz(CACHE/'graph.npz')
        assignment=np.load(CACHE/f'{args.suffix}.npy')
    else:
        pop=c['pop'];votes=c['votes'];edges=c['edges'];graph=load_npz(CACHE/'coarse-graph.npz')
        assignment=np.load(CACHE/'coarse-candidate.npy') if args.resume else c['assignment'].copy()
    if args.election!='all':
        elections=json.loads((CACHE/'elections.json').read_text());idx=next(i for i,e in enumerate(elections) if e['id']==args.election)
        votes=votes[:,[idx],:].copy()
    log=[]
    start=time.time()
    for epoch in range(args.epochs):
        progress=epoch/max(1,args.epochs-1)
        temp=.003*(1-progress)**2+.000002 if not args.blocks else .00003*(1-progress)**2+.00000001
        weight=args.population_weight
        slack=.02 if not args.blocks else .021
        assignment,accepted,dp,dv,cost=anneal(assignment,pop,votes,graph.indptr,graph.indices,edges,args.attempts,args.seed+epoch,temp,weight,slack)
        s=stats(dp,dv,cost);s.update(epoch=epoch,accepted=int(accepted),seconds=round(time.time()-start,2),seed=args.seed+epoch,attempts=args.attempts,temperature=temp,population_weight=weight,objective=args.election)
        log.append(s);print(json.dumps(s),flush=True)
        if args.blocks:
            np.save(CACHE/f'{args.suffix}.npy',assignment)
        else:
            np.save(CACHE/'coarse-candidate.npy',assignment)
            np.save(CACHE/'candidate.npy',assignment[c['groups']])
        write_json(CACHE/(f'block-search-{args.suffix}-log.json' if args.blocks else 'search-log.json'),log)

if __name__=='__main__': main()
