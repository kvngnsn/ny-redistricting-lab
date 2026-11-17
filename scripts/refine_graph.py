"""Deterministically subdivide coarse units into smaller connected block groups."""
import argparse
import numpy as np
from numba import njit
from scipy.sparse import coo_matrix,load_npz,save_npz
from common import CACHE

@njit(cache=True)
def group_blocks(original,pop,indptr,indices,maxpop,maxnodes):
    n=len(pop);groups=np.full(n,-1,np.int32);queue=np.empty(n,np.int32);count=0
    for start in range(n):
        if groups[start]>=0:continue
        groups[start]=count;queue[0]=start;head=0;tail=1;total=pop[start]
        while head<tail:
            u=queue[head];head+=1
            for j in indices[indptr[u]:indptr[u+1]]:
                if groups[j]<0 and original[j]==original[start] and total+pop[j]<=maxpop and tail<maxnodes:
                    groups[j]=count;queue[tail]=j;tail+=1;total+=pop[j]
        count+=1
    return groups,count

def main():
    p=argparse.ArgumentParser();p.add_argument('--name',default='fine');p.add_argument('--max-pop',type=int,default=500);p.add_argument('--max-blocks',type=int,default=20);args=p.parse_args()
    c=np.load(CACHE/'coarse.npz');b=np.load(CACHE/'blocks.npz');v=np.load(CACHE/'votes.npy');g=load_npz(CACHE/'graph.npz');edges=np.load(CACHE/'edges.npy')
    groups,n=group_blocks(c['groups'],b['pop'],g.indptr,g.indices,args.max_pop,args.max_blocks)
    pop=np.bincount(groups,weights=b['pop']).astype(np.int64);votes=np.zeros((n,13,3),np.int64);np.add.at(votes,groups,v)
    parent=np.zeros(n,np.int32);parent[groups]=c['groups'];assignment=np.zeros(n,np.int16);assignment[groups]=b['baseline']
    e=np.sort(groups[edges],axis=1);e=np.unique(e[e[:,0]!=e[:,1]],axis=0).astype(np.int32)
    graph=coo_matrix((np.ones(len(e)*2,np.int8),(np.r_[e[:,0],e[:,1]],np.r_[e[:,1],e[:,0]])),shape=(n,n)).tocsr()
    np.savez_compressed(CACHE/f'{args.name}.npz',pop=pop,votes=votes,groups=groups,parent=parent,assignment=assignment,edges=e)
    save_npz(CACHE/f'{args.name}-graph.npz',graph)
    print('Refined units',n,'edges',len(e),'population',pop.sum())
if __name__=='__main__':main()
