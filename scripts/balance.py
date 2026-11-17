"""Exact integer balancing through connected-core, bidirectional subset-sum moves.

Uses safe free-block pools from connected_core. A bitset dynamic program
finds an exact net population transfer, allowing opposite-direction block swaps.
"""
import argparse,json,time
from collections import deque,defaultdict
import numpy as np
from scipy.sparse import load_npz
from connected_core import make_pool
from common import CACHE,write_json
from numba import njit
from optimize import donor_connected

@njit(cache=True)
def shake_zeros(a,pop,indptr,indices,edges,seed):
    np.random.seed(seed);n=len(a);visited=np.zeros(n,np.int64);queue=np.empty(n,np.int32);accepted=0
    for step in range(1000000):
        edge=edges[np.random.randint(len(edges))];i,j=edge[0],edge[1]
        if np.random.random()<.5:i,j=j,i
        if a[i]!=a[j] and pop[i]==0 and donor_connected(i,int(a[i]),a,indptr,indices,visited,step+1,queue):
            a[i]=a[j];accepted+=1
    return accepted

def subset(weights,target,limit=30000):
    limit=max(limit,abs(target)*2+1000)
    mask=(1<<(2*limit+1))-1;states=[1<<limit]
    for k,w in enumerate(weights):
        old=states[-1];new=old|((old<<w) if w>0 else (old>>(-w)));new&=mask;states.append(new)
        if (new>>(target+limit))&1:
            remaining=target;selected=[]
            for j in range(k,-1,-1):
                if not ((states[j]>>(remaining+limit))&1):selected.append(j);remaining-=weights[j]
            assert remaining==0
            return selected,target
    possible=states[-1] & (((1<<(target+limit+1))-1)^((1<<(limit+1))-1))
    if possible:
        best=possible.bit_length()-1-limit
        remaining=best;selected=[]
        for j in range(len(weights)-1,-1,-1):
            if not ((states[j]>>(remaining+limit))&1):selected.append(j);remaining-=weights[j]
        assert remaining==0
        return selected,best
    return None

def main():
    p=argparse.ArgumentParser();p.add_argument('--name',default='candidate');p.add_argument('--seed',type=int,default=37000);p.add_argument('--rounds',type=int,default=30);args=p.parse_args()
    b=np.load(CACHE/'blocks.npz');pop=b['pop'];a=np.load(CACHE/f'{args.name}.npy');graph=load_npz(CACHE/'graph.npz')
    dp=np.bincount(a,weights=pop,minlength=26).astype(np.int64);initial=dp.copy()
    target=np.full(26,int(pop.sum()//26),np.int64);target[np.argsort(-dp,kind='stable')[:int(pop.sum()%26)]]+=1
    start=time.time();moves=[];zero_moves=[];edges=np.load(CACHE/'edges.npy')
    for r in range(args.rounds):
        if r:zero_moves.append(int(shake_zeros(a,pop,graph.indptr,graph.indices,edges,args.seed+10000+r)))
        core,pool=make_pool(a,graph.indptr,graph.indices,args.seed+r)
        allowed={int(i):set(core[graph.indices[graph.indptr[i]:graph.indptr[i+1]]])-{np.int16(-1)} for i in np.flatnonzero(pool&(pop>0))}
        for step in range(1000):
            error=dp-target
            if not np.any(error):break
            boundary=defaultdict(list)
            for i,targets in allowed.items():
                for d in targets:
                    if d!=a[i]:boundary[int(a[i]),int(d)].append(i)
            adjacency=[set() for _ in range(26)];reverse=[set() for _ in range(26)]
            for (x,y),nodes in boundary.items():
                if nodes:adjacency[x].add(y);reverse[y].add(x)
            distance=np.full(26,999);q=deque(np.flatnonzero(error<0).tolist())
            for d in q:distance[d]=0
            while q:
                x=q.popleft()
                for y in reverse[x]:
                    if distance[y]>distance[x]+1:distance[y]=distance[x]+1;q.append(y)
            changed=False
            for x in sorted(np.flatnonzero(error>0),key=lambda x:-error[x]):
                for y in sorted(adjacency[x],key=lambda y:(distance[y],error[y])):
                    if distance[y]>=distance[x]:continue
                    amount=int(error[x]);amount=min(amount,int(-error[y])) if error[y]<0 else amount
                    nodes=list(boundary[x,y])+list(boundary[y,x])
                    # Small blocks first keeps changed population and runtime modest.
                    nodes.sort(key=lambda i:(int(pop[i]),i))
                    weights=[int(pop[i])*(1 if a[i]==x else -1) for i in nodes]
                    chosen=subset(weights,amount)
                    if chosen is None:continue
                    chosen,amount=chosen
                    for j in chosen:
                        i=nodes[j];a[i]=y if a[i]==x else x
                    dp[x]-=amount;dp[y]+=amount;changed=True
                    moves.append({'from':int(x+1),'to':int(y+1),'net_people':amount,'blocks':len(chosen),'round':r})
                    break
                if changed:break
            if not changed:break
        print('Balance',args.name,r,'absolute error',int(np.abs(dp-target).sum()),'moves',len(moves),'errors',(dp-target).tolist(),flush=True)
        if np.array_equal(dp,target):
            np.save(CACHE/f'{args.name}.npy',a)
            report={'method':'connected fixed cores + bidirectional subset-sum transfers','seed':args.seed,'rounds':r+1,'initial_populations':initial.tolist(),'target_populations':target.tolist(),'final_populations':dp.tolist(),'population_range':int(dp.max()-dp.min()),'exact':True,'seconds':round(time.time()-start,3),'zero_population_moves_by_round':zero_moves,'moves':moves}
            write_json(CACHE/f'balance-{args.name}-log.json',report);print(json.dumps({k:v for k,v in report.items() if k!='moves'}),flush=True);return
    raise SystemExit('No exact solution; no assignment file was changed')
if __name__=='__main__':main()
