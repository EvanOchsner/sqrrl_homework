#! /usr/bin/env python

"""
Sanity check and summarize output from a chunk. Plot S/F rates.
"""

import numpy as np
import cPickle as pickle
import os
from pylab import plt

# N.B. Hardcoded to study first chunk.
# Change next line to study another chunk.
# Change paths below if you store data elsewhere
FNAME='x00000'

fname = '../data/intermediate_data/' + FNAME + '_counts.p'
with open(fname, 'rb') as f:
    NS, NF, S_d, F_d = pickle.load(f)

fname = '../data/intermediate_data/' + FNAME + '_arrays.p'
with open(fname, 'rb') as f:
    S_arr, F_arr = pickle.load(f)

assert NS==len(S_arr)
assert NF==len(F_arr)

S_per_k = []
F_per_k = []
for k in S_d.keys():
    S_per_k.append(S_d[k])
for k in F_d.keys():
    F_per_k.append(F_d[k])

NSv = np.sum(S_per_k)
NFv = np.sum(F_per_k)
Smax = np.max(S_per_k)
Fmax = np.max(F_per_k)

assert NS==NSv
assert NF==NFv

print "Successes: %i" % NS
print "Failures: %i" % NF

print "Unique successful keys: %i" % len(S_d.keys()) 
print "Unique failed keys: %i" % len(F_d.keys())

cnt = 0
for k in F_d.keys():
    if k in S_d.keys():
        cnt += 1 

print "Keys with Success and Failure: %i" % cnt

ST = np.transpose(S_arr)
FT = np.transpose(F_arr)

St, Scounts = np.unique(ST[0], return_counts=True)
Ft, Fcounts = np.unique(FT[0], return_counts=True)

print "Most Successes for one key: %i" % Smax
print "Most Failures for one key: %i" % Fmax

print "Most Successes in one second: %i" % np.max(Scounts)
print "Most Failures in one second: %i" % np.max(Fcounts)


Stimes = St.astype(int)
Ftimes = Ft.astype(int)

plt.plot(Stimes, Scounts, 'b.', label='Success')
plt.plot(Ftimes, Fcounts, 'r.', label='Fail')
plt.legend()
plt.yscale('log')
plt.xlabel('Time (sec)')
plt.ylabel('Rate (events/sec)')
fname = '../data/summary_data/rate_' + FNAME + '.png'
plt.savefig(fname)
plt.show()
