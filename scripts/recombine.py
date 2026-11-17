"""Tree recombination explores connected alternatives beyond local boundary flips.

The heuristic merges adjacent districts, builds a randomized spanning tree, and
evaluates population-balanced tree cuts. It is not a uniform plan sampler.
"""
import argparse,json,time
import numpy as np
from numba import njit
from scipy.sparse import load_npz
from common import CACHE,write_json
from optimize import partisan_cost,stats,anneal

@njit(cache=True)
def recombine(a,pop,votes,indptr,indices,edges,attempts,seed,temp,slack):
    np.random.seed(seed)
    n,ne=len(a),votes.shape[1]
    target=pop.sum()/26
    dp=np.zeros(26,np.int64);dv=np.zeros((26,ne,3),np.float64)
    for i in range(n): dp[a[i]]+=pop[i];dv[a[i]]+=votes[i]
    visited=np.zeros(n,np.int64);parent=np.empty(n,np.int32);order=np.empty(n,np.int32)
    stack=np.empty(n,np.int32);sp=np.empty(n,np.int64);sv=np.empty((n,ne,3),np.float64)
    in_subtree=np.zeros(n,np.int64)
    accepted=0
    for step in range(attempts):
        start=-1
        for z in range(200):
            edge=edges[np.random.randint(len(edges))]
            x,y=a[edge[0]],a[edge[1]]
            if x!=y: start=edge[0];break
        if start<0:continue
        stamp=step+1
        visited[start]=stamp;parent[start]=-1;stack[0]=start;top=1;count=0
        while top>0:
            top-=1;u=stack[top];order[count]=u;count+=1
            sp[u]=pop[u];sv[u]=votes[u]
            degree=indptr[u+1]-indptr[u]
            if degree==0:continue
            offset=np.random.randint(degree)
            for kk in range(degree):
                v=indices[indptr[u]+(kk+offset)%degree]
                if (a[v]==x or a[v]==y) and visited[v]!=stamp:
                    visited[v]=stamp;parent[v]=u;stack[top]=v;top+=1
        for k in range(count-1,0,-1):
            u=order[k];v=parent[u];sp[v]+=sp[u];sv[v]+=sv[u]
        totalp=sp[start];totalv=sv[start].copy()
        oldcost=partisan_cost(dv[x])+partisan_cost(dv[y])
        best=1e100;cut=-1
        for k in range(1,count):
            u=order[k];pa=sp[u];pb=totalp-pa
            if abs(pa-target)>target*slack or abs(pb-target)>target*slack:continue
            score=partisan_cost(sv[u])+partisan_cost(totalv-sv[u])
            score+=10000*(((pa-target)/target)**2+((pb-target)/target)**2)
            # Tiny continuous noise avoids deterministic tie fixation.
            score+=np.random.random()*temp*.05
            if score<best:best=score;cut=u
        oldcost+=10000*(((dp[x]-target)/target)**2+((dp[y]-target)/target)**2)
        if cut<0:continue
        delta=best-oldcost
        if delta>0 and np.random.random()>=np.exp(-delta/max(temp,1e-12)):continue
        # Descendant membership follows the rooted tree in parent-before-child order.
        for k in range(count):
            u=order[k]
            if u==cut or (parent[u]>=0 and in_subtree[parent[u]]==stamp):in_subtree[u]=stamp
            a[u]=x if in_subtree[u]==stamp else y
        dp[x]=sp[cut];dp[y]=totalp-sp[cut];dv[x]=sv[cut];dv[y]=totalv-sv[cut]
        accepted+=1
    cost=0.
    for d in range(26):cost+=partisan_cost(dv[d])
    return a,accepted,dp,dv,cost

def main():
    p=argparse.ArgumentParser();p.add_argument('--rounds',type=int,default=40);p.add_argument('--attempts',type=int,default=2000);p.add_argument('--seed',type=int,default=5200)
    p.add_argument('--election',default='all');p.add_argument('--suffix',default='candidate');p.add_argument('--init',default='coarse-candidate.npy')
    args=p.parse_args();c=np.load(CACHE/'coarse.npz');g=load_npz(CACHE/'coarse-graph.npz')
    selected_votes=c['votes']
    if args.election!='all':
        elections=json.loads((CACHE/'elections.json').read_text());idx=next(i for i,e in enumerate(elections) if e['id']==args.election)
        selected_votes=selected_votes[:,[idx],:].copy()
    a=np.load(CACHE/args.init);log=[];start=time.time()
    for r in range(args.rounds):
        temperature=.2*(1-r/max(args.rounds-1,1))+.0001
        a,accepted,dp,dv,cost=recombine(a,c['pop'],selected_votes,g.indptr,g.indices,c['edges'],args.attempts,args.seed+r,temperature,.005)
        a,flips,dp,dv,cost=anneal(a,c['pop'],selected_votes,g.indptr,g.indices,c['edges'],2000000,args.seed+10000+r,.0005,10000.,.02)
        s=stats(dp,dv,cost);s.update(round=r,recombinations=int(accepted),flips=int(flips),seconds=round(time.time()-start,2),seed=args.seed+r,attempts=args.attempts,temperature=temperature)
        s['objective']=args.election;log.append(s);print(json.dumps(s),flush=True)
        np.save(CACHE/f'coarse-{args.suffix}.npy',a);np.save(CACHE/f'{args.suffix}.npy',a[c['groups']]);write_json(CACHE/f'recombination-{args.suffix}-log.json',log)

if __name__=='__main__':main()
