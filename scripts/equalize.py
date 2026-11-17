"""Search for equal district two-party margins, targeting the statewide margin.

The objective penalizes deviations on both sides of the target. Search-time
population tolerances are temporary; published plans require exact finishing.
"""
import argparse,json,time
import numpy as np
from numba import njit
from scipy.sparse import load_npz
from common import CACHE,write_json
from optimize import donor_connected

@njit(cache=True)
def cost(d,r,target,power):
    error=(d-r)/max(d+r,1.)-target
    return error*error + power*error**4

@njit(cache=True)
def totals(a,pop,d,r):
    dp=np.zeros(26,np.int64);dd=np.zeros(26,np.int64);rr=np.zeros(26,np.int64)
    for i in range(len(a)):
        x=a[i];dp[x]+=pop[i];dd[x]+=d[i];rr[x]+=r[i]
    return dp,dd,rr

@njit(cache=True)
def flips(a,pop,d,r,indptr,indices,edges,attempts,seed,temp,weight,slack,power,zero_skip=0.):
    np.random.seed(seed);n=len(a);target=(d.sum()-r.sum())/(d.sum()+r.sum());ideal=pop.sum()/26.
    dp,dd,rr=totals(a,pop,d,r);visited=np.zeros(n,np.int64);queue=np.empty(n,np.int32);accepted=0
    for step in range(attempts):
        edge=edges[np.random.randint(len(edges))];i,j=edge[0],edge[1]
        if np.random.random()<.5:i,j=j,i
        x,y=a[i],a[j]
        if x==y:continue
        if zero_skip>0 and pop[i]==0 and d[i]+r[i]==0 and np.random.random()<zero_skip:continue
        pa,pb=dp[x]-pop[i],dp[y]+pop[i]
        if abs(pa-ideal)>ideal*slack and abs(pa-ideal)>=abs(dp[x]-ideal):continue
        if abs(pb-ideal)>ideal*slack and abs(pb-ideal)>=abs(dp[y]-ideal):continue
        da,db=dd[x]-d[i],dd[y]+d[i];ra,rb=rr[x]-r[i],rr[y]+r[i]
        delta=cost(da,ra,target,power)+cost(db,rb,target,power)-cost(dd[x],rr[x],target,power)-cost(dd[y],rr[y],target,power)
        delta+=weight*((pa-ideal)**2+(pb-ideal)**2-(dp[x]-ideal)**2-(dp[y]-ideal)**2)/(ideal*ideal)
        if delta>0 and np.random.random()>=np.exp(-delta/max(temp,1e-14)):continue
        if not donor_connected(i,int(x),a,indptr,indices,visited,step+1,queue):continue
        a[i]=y;dp[x],dp[y]=pa,pb;dd[x],dd[y]=da,db;rr[x],rr[y]=ra,rb;accepted+=1
    return a,accepted

@njit(cache=True)
def trees(a,pop,d,r,indptr,indices,edges,attempts,seed,temp,weight,slack,power):
    np.random.seed(seed);n=len(a);target=(d.sum()-r.sum())/(d.sum()+r.sum());ideal=pop.sum()/26.
    dp,dd,rr=totals(a,pop,d,r)
    visited=np.zeros(n,np.int64);parent=np.empty(n,np.int32);order=np.empty(n,np.int32);stack=np.empty(n,np.int32)
    sp=np.empty(n,np.int64);sd=np.empty(n,np.int64);sr=np.empty(n,np.int64);membership=np.zeros(n,np.int64);accepted=0
    for step in range(attempts):
        start=-1
        for z in range(200):
            edge=edges[np.random.randint(len(edges))];x,y=a[edge[0]],a[edge[1]]
            if x!=y:start=edge[0];break
        if start<0:continue
        stamp=step+1;visited[start]=stamp;parent[start]=-1;stack[0]=start;top=1;count=0
        while top>0:
            top-=1;u=stack[top];order[count]=u;count+=1;sp[u]=pop[u];sd[u]=d[u];sr[u]=r[u]
            degree=indptr[u+1]-indptr[u]
            if degree==0:continue
            offset=np.random.randint(degree)
            for k in range(degree):
                v=indices[indptr[u]+(k+offset)%degree]
                if (a[v]==x or a[v]==y) and visited[v]!=stamp:
                    visited[v]=stamp;parent[v]=u;stack[top]=v;top+=1
        for k in range(count-1,0,-1):
            u=order[k];v=parent[u];sp[v]+=sp[u];sd[v]+=sd[u];sr[v]+=sr[u]
        tp,td,tr=sp[start],sd[start],sr[start]
        best=1e100;cut=-1
        for k in range(1,count):
            u=order[k];pa=sp[u];pb=tp-pa
            if abs(pa-ideal)>ideal*slack or abs(pb-ideal)>ideal*slack:continue
            score=cost(sd[u],sr[u],target,power)+cost(td-sd[u],tr-sr[u],target,power)
            score+=weight*((pa-ideal)**2+(pb-ideal)**2)/(ideal*ideal)
            if score<best:best=score;cut=u
        if cut<0:continue
        before=cost(dd[x],rr[x],target,power)+cost(dd[y],rr[y],target,power)+weight*((dp[x]-ideal)**2+(dp[y]-ideal)**2)/(ideal*ideal)
        delta=best-before
        if delta>0 and np.random.random()>=np.exp(-delta/max(temp,1e-14)):continue
        for k in range(count):
            u=order[k]
            if u==cut or (parent[u]>=0 and membership[parent[u]]==stamp):membership[u]=stamp
            a[u]=x if membership[u]==stamp else y
        dp[x],dp[y]=sp[cut],tp-sp[cut];dd[x],dd[y]=sd[cut],td-sd[cut];rr[x],rr[y]=sr[cut],tr-sr[cut];accepted+=1
    return a,accepted

def metrics(a,pop,d,r):
    dp,dd,rr=totals(a,pop,d,r);m=(dd-rr)/(dd+rr);target=float((d.sum()-r.sum())/(d.sum()+r.sum()));error=m-target
    return {'statewide_margin':target,'minimum_margin':float(m.min()),'maximum_margin':float(m.max()),'maximum_error_pp':float(np.abs(error).max()*100),'rms_error_pp':float(np.sqrt(np.mean(error**2))*100),'margins':m.tolist(),'democratic_leads':int((m>0).sum()),'population_range':int(dp.max()-dp.min())}

def main():
    p=argparse.ArgumentParser();p.add_argument('--name',default='equalized');p.add_argument('--init',default='coarse-sweep.npy');p.add_argument('--rounds',type=int,default=300);p.add_argument('--attempts',type=int,default=5000);p.add_argument('--flips',type=int,default=1000000);p.add_argument('--seed',type=int,default=81000);p.add_argument('--power',type=float,default=10.);p.add_argument('--blocks',action='store_true');p.add_argument('--graph-prefix',default='coarse');p.add_argument('--temperature',type=float,default=.003);p.add_argument('--population-weight',type=float,default=100.);p.add_argument('--slack',type=float,default=.02);p.add_argument('--end-weight',type=float);p.add_argument('--end-slack',type=float,default=.01);p.add_argument('--zero-vote-skip',type=float,default=0.);p.add_argument('--stop-after',type=int);args=p.parse_args()
    if args.blocks:
        b=np.load(CACHE/'blocks.npz');pop=b['pop'];v=np.load(CACHE/'votes.npy');edges=np.load(CACHE/'edges.npy');g=load_npz(CACHE/'graph.npz');groups=None
    else:
        b=np.load(CACHE/f'{args.graph_prefix}.npz');pop=b['pop'];v=b['votes'];edges=b['edges'];g=load_npz(CACHE/f'{args.graph_prefix}-graph.npz');groups=b['groups']
    d=v[:,-1,0].copy();r=v[:,-1,1].copy();a=np.load(CACHE/args.init).copy()
    assert len(a)==len(pop)
    log=[];start=time.time();best=1e100
    write_json(CACHE/f'equalize-{args.name}-config.json',vars(args))
    for step in range(args.rounds):
        fraction=step/max(1,args.rounds-1);temp=args.temperature*(1-fraction)**2+1e-9;weight=args.population_weight if args.end_weight is None else args.population_weight*(args.end_weight/args.population_weight)**fraction
        slack=args.slack*(1-fraction)+args.end_slack*fraction
        a,recom=trees(a,pop,d,r,g.indptr,g.indices,edges,args.attempts,args.seed+step,temp,weight,slack/2,args.power)
        a,accepted=flips(a,pop,d,r,g.indptr,g.indices,edges,args.flips,args.seed+100000+step,temp*.03,weight,slack,args.power,args.zero_vote_skip)
        m=metrics(a,pop,d,r);m.update(round=step,recombinations=int(recom),flips=int(accepted),seconds=round(time.time()-start,2),temperature=temp,population_weight=weight,population_slack=slack)
        log.append(m);print(json.dumps(m),flush=True)
        np.save(CACHE/f'{args.name}.npy',a if groups is None else a[groups])
        np.save(CACHE/f'{args.graph_prefix}-{args.name}.npy',a)
        if m['maximum_error_pp']<best:
            best=m['maximum_error_pp'];np.save(CACHE/f'{args.name}-best.npy',a if groups is None else a[groups]);np.save(CACHE/f'{args.graph_prefix}-{args.name}-best.npy',a)
        write_json(CACHE/f'equalize-{args.name}-log.json',log)
        if args.stop_after is not None and step+1>=args.stop_after:break
if __name__=='__main__':main()
