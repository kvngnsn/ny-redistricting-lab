"""Joint boundary-block reassignment on connected fixed cores.

Minimize the maximum partisan-surplus error, normalized by each district's
pre-move two-party turnout. Recompute real margins after every integer solution.
"""
import argparse,json,time
import numpy as np
from scipy.sparse import load_npz,coo_matrix
from scipy.optimize import milp,Bounds,LinearConstraint
from connected_core import make_pool
from common import CACHE,write_json
from equalize import metrics

def main():
    p=argparse.ArgumentParser();p.add_argument('--name',default='equal-pool');p.add_argument('--init',required=True);p.add_argument('--rounds',type=int,default=30);p.add_argument('--seconds',type=float,default=20);p.add_argument('--seed',type=int,default=141000);p.add_argument('--population-slack',type=int,default=3000);args=p.parse_args()
    b=np.load(CACHE/'blocks.npz');pop=b['pop'];v=np.load(CACHE/'votes.npy');d=v[:,-1,0];r=v[:,-1,1];turnout=d+r;target=(d.sum()-r.sum())/turnout.sum();surplus=d-r-target*turnout
    a=np.load(CACHE/args.init).copy();g=load_npz(CACHE/'graph.npz');ideal=pop.sum()/26.;start=time.time();log=[];best=1e100
    np.save(CACHE/f'{args.name}-start.npy',a);write_json(CACHE/f'{args.name}-config.json',vars(args))
    for step in range(args.rounds):
        core,pool=make_pool(a,g.indptr,g.indices,args.seed+step)
        nodes=[];dest=[]
        for i in np.flatnonzero(pool):
            for y in sorted(set(core[g.indices[g.indptr[i]:g.indptr[i+1]]])):
                if y>=0 and y!=a[i]:nodes.append(i);dest.append(y)
        nodes=np.array(nodes,np.int32);dest=np.array(dest,np.int16);m=len(nodes);cols=np.arange(m);_,group=np.unique(nodes,return_inverse=True);ng=group.max()+1
        dp=np.bincount(a,weights=pop,minlength=26);ss=np.bincount(a,weights=surplus,minlength=26);vv=np.bincount(a,weights=turnout,minlength=26)
        rows=np.r_[a[nodes],dest,26+a[nodes],26+dest,52+a[nodes],52+dest,78+group,np.arange(26,78)]
        columns=np.r_[cols,cols,cols,cols,cols,cols,cols,np.full(52,m)]
        values=np.r_[-pop[nodes],pop[nodes],-surplus[nodes],surplus[nodes],surplus[nodes],-surplus[nodes],np.ones(m),-vv,-vv]
        matrix=coo_matrix((values,(rows,columns)),shape=(78+ng,m+1)).tocsc()
        # If an input district is outside the finishing band, permit only an
        # improvement toward it; then tighten to the common band on later rounds.
        lo=np.minimum(ideal-args.population_slack,dp)-dp;hi=np.maximum(ideal+args.population_slack,dp)-dp
        low=np.r_[lo,np.full(52,-np.inf),np.zeros(ng)];high=np.r_[hi,-ss,ss,np.ones(ng)]
        objective=np.r_[pop[nodes]*1e-12,1.];integrality=np.r_[np.ones(m),0]
        before=metrics(a,pop,d,r);print('Pool',step,'variables',m,'gap',before['maximum_error_pp'],flush=True)
        result=milp(objective,integrality=integrality,bounds=Bounds(np.zeros(m+1),np.ones(m+1)),constraints=LinearConstraint(matrix,low,high),options={'time_limit':args.seconds,'mip_rel_gap':.01})
        accepted=False;changed=0
        if result.x is not None:
            indices=np.flatnonzero(result.x[:m]>.5);out=a.copy();out[nodes[indices]]=dest[indices];after=metrics(out,pop,d,r)
            if after['maximum_error_pp']<before['maximum_error_pp']-1e-9:
                a=out;accepted=True;changed=len(indices)
        stat=metrics(a,pop,d,r);stat.update(round=step,seed=args.seed+step,variables=m,status=int(result.status),accepted=accepted,changed_blocks=changed,seconds=round(time.time()-start,2));log.append(stat)
        print(json.dumps(stat),flush=True);np.save(CACHE/f'{args.name}.npy',a);write_json(CACHE/f'{args.name}-log.json',log)
        if stat['maximum_error_pp']<best:best=stat['maximum_error_pp'];np.save(CACHE/f'{args.name}-best.npy',a)
if __name__=='__main__':main()
