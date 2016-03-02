#! /usr/bin/env python

"""
Process the first chunk of the auth log. Do not attempt to classify it,
but create the counts data that will be used to compute likelihoods
for the next chunk.

Also, study and plot some features of the first dataset.
"""

import bayes_class
import numpy as np
import cPickle as pickle
import os

# initialize classifier with prior ratio = 0., don't predict result
# We will study the first chunk to learn the prior
ac = bayes_class.AuthClassifier(prior_ratio=0.,
        predict=False, full_tabulate=True)

# N.B. Change next line if first input data chunk stored elsewhere,
# or was given a different name
fname = '../data/input_data/x00000'
ac.process_chunk(fname)

# Write output data
# N.B. Change args if you want to store outputs elsewhere
ac.pickle_current_counts('../data/intermediate_data/x00000_counts.p')
ac.pickle_current_arrays('../data/intermediate_data/x00000_arrays.p')
ac.write_summary('../data/summary_data/summary_x00000.json')
