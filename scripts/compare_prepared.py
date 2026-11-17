"""Compare a fresh, original-source preparation with the published numerical model."""
import numpy as np
from common import CACHE,ROOT
b=np.load(CACHE/'blocks.npz',allow_pickle=False);published=np.load(ROOT/'research/model-inputs.npz',allow_pickle=False)
for key in b.files:
    assert np.array_equal(b[key],published[key]),f'Prepared block array differs: {key}'
assert np.array_equal(np.load(CACHE/'votes.npy'),published['votes']),'Prepared votes differ'
actual=np.load(CACHE/'edges.npy');expected=published['edges']
a=actual[np.lexsort((actual[:,1],actual[:,0]))];e=expected[np.lexsort((expected[:,1],expected[:,0]))]
assert np.array_equal(a,e),'Prepared adjacency differs'
assert np.array_equal(np.load(CACHE/'nyt-precinct-assignments.npy'),published['nyt_precinct']),'Precinct crosswalk differs'
print('Prepared source model exactly matches all published block, vote, edge and precinct arrays.')
