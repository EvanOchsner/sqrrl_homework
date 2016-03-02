#! /usr/bin/env python

"""
Process one or more chunks of the auth log through the classifier and predict
the result of each event.
"""

import bayes_class
import os
import json
from optparse import OptionParser

def compute_prior(chunk_number, summ_dir, verbose=False):
    """
    Read all summary JSON files stored under summ_dir with suffix less than
    chunk_number, sum up total S/F counts, compute prior ratio = p(F) / p(S)
    """
    prior_NS = 0
    prior_NF = 0
    for chunk in range(0,chunk_number):
        summary_name = str("summary_x%05d.json" % chunk)
        fname = os.path.join(summ_dir, summary_name)
        with open(fname, 'r') as f:
            summary_d = json.load(f)
        prior_NS += summary_d["results"]["Success"]
        prior_NF += summary_d["results"]["Fail"]
    prior_ratio = float(prior_NF) / float(prior_NS)
    if verbose:
        print "Found %i previous successes and %i previous failures" % (prior_NS, prior_NF)
        print "This gives prior ratio p(F)/p(S) = %f" % prior_ratio
    return prior_ratio

usage="Usage message... ADDME"
parser = OptionParser(usage=usage)
parser.add_option("-s", "--start-chunk", default=1, type=int,
        help="Number of first chunk to analyze")
parser.add_option("-e", "--end-chunk", default=1, type=int,
        help="Number of last chunk to analyze")
parser.add_option("-f", "--full-tabulate", default=False,
        action="store_true")
parser.add_option("-i", "--input-dir", default='../data/input_data',
        help="Directory where input data chunks are stored")
parser.add_option("-I", "--intermediate-dir",
        default='../data/intermediate_data',
        help="Directory to store intermediate pickled data")
parser.add_option("-S", "--summary-dir", default='../data/summary_data',
        help="Directory where summary output data is stored")
opts, args = parser.parse_args()


assert opts.start_chunk > 0
assert opts.end_chunk >= opts.start_chunk

prior_ratio = compute_prior(opts.start_chunk, opts.summary_dir, True)

ac = bayes_class.AuthClassifier(prior_ratio=prior_ratio,
        predict=True, full_tabulate=opts.full_tabulate)

# Read in pickled counts for chunk just before starting chunk
prev_pickle = str("x%05d_counts.p" % (opts.start_chunk-1) )
fname = os.path.join(opts.intermediate_dir, prev_pickle)
print "Reading previous counts from %s" % fname
ac.previous_counts_from_pickle(fname)

for chunk in range(opts.start_chunk, (opts.end_chunk+1)):
    fname = os.path.join(opts.input_dir, str("x%05d" % chunk))
    print "Processing chunk %s" % fname
    ac.process_chunk(fname)
    fname = os.path.join(opts.intermediate_dir, str("x%05d_counts.p" % chunk) )
    print "Pickling counts as %s" % fname
    ac.pickle_current_counts(fname)
    if opts.full_tabulate:
        fname = os.path.join(opts.intermediate_dir, str("x%05d_arrays.p" % chunk) )
        print "Pickling result arrays as %s" % fname
        ac.pickle_current_arrays(fname)
    fname = os.path.join(opts.summary_dir, str("summary_x%05d.json" % chunk) )
    print "Writing summary file %s" % fname
    ac.write_summary(fname)
    # Update the prior and use pickle to move curr counts to prev counts
    prior_ratio = compute_prior(chunk+1, opts.summary_dir, True)
    fname = os.path.join(opts.intermediate_dir, str("x%05d_counts.p" % chunk) )
    ac.reset(prior_ratio)
    #ac.reset_from_pickle(prior_ratio, fname)
