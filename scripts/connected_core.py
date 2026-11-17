"""Extract movable boundary blocks while preserving connected fixed cores."""
import numpy as np
from numba import njit
from optimize import donor_connected

@njit(cache=True)
def make_pool(a,indptr,indices,seed):
    np.random.seed(seed);core=a.copy();n=len(a)
    visited=np.zeros(n,np.int64);queue=np.empty(n,np.int32)
    order=np.random.permutation(n);removed=np.zeros(n,np.bool_)
    for k in range(n):
        i=order[k];boundary=False
        for j in indices[indptr[i]:indptr[i+1]]:
            if a[j]!=a[i]:boundary=True;break
        safe=boundary
        if safe:
            for j in indices[indptr[i]:indptr[i+1]]:
                if removed[j] and a[j]==a[i]:
                    attached=False
                    for w in indices[indptr[j]:indptr[j+1]]:
                        if w!=i and core[w]==a[j]:attached=True;break
                    if not attached:safe=False;break
        if safe and donor_connected(i,int(a[i]),core,indptr,indices,visited,k+1,queue):
            core[i]=-1;removed[i]=True
    return core,removed
