#! /usr/bin/env python

"""
Read in Summary JSON files, tally Success/Fail and prediction results
"""

import os
import json
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-s", "--start-chunk", default=0, type=int,
        help="Number of first summary file")
parser.add_option("-e", "--end-chunk", default=1051, type=int,
        help="Number of last summary file")
parser.add_option("-S", "--summary-dir", default='../data/summary_data',
        help="Directory where summary output data is stored")
parser.add_option("-o", "--output",
        default='../data/summary_data/final_summary.json',
        help="Directory where summary output data is stored")
opts, args = parser.parse_args()

NS = NF = CS = CF = IS = IF = 0
for n in range(opts.start_chunk, opts.end_chunk+1):
    summary_name = str("summary_x%05d.json" % n)
    fname = os.path.join(opts.summary_dir, summary_name)
    with open(fname, 'r') as f:
        summ_d = json.load(f)
        NS += summ_d["results"]["Success"]
        NF += summ_d["results"]["Fail"]
        try:
            CS += summ_d["predictions"]["Correct_Success"]
            CF += summ_d["predictions"]["Correct_Fail"]
            IS += summ_d["predictions"]["Incorrect_Success"]
            IF += summ_d["predictions"]["Incorrect_Fail"]
        except KeyError:
            pass

total_correct = CS + CF
total_incorrect = IS + IF
total_guesses = CS + CF + IS + IF
CS_percent = 100. * float(CS) / float(total_guesses)
CF_percent = 100. * float(CF) / float(total_guesses)
IS_percent = 100. * float(IS) / float(total_guesses)
IF_percent = 100. * float(IF) / float(total_guesses)
C_percent = 100. * float(CS + CF) / float(total_guesses)
I_percent = 100. * float(IS + IF) / float(total_guesses)

print "Total Successes: %i" % NS
print "Total Failures: %i" % NF
print "Total predictions made: %i" % total_guesses
print "Correct Success predictions: %i (%.2f%%)" % (CS, CS_percent)
print "Correct Fail predictions: %i (%.2f%%)" % (CF, CF_percent)
print "Incorrect Success predictions (result was Fail): %i (%.2f%%)" % (IS, IS_percent)
print "Incorrect Fail predictions (result was Success): %i (%.2f%%)" % (IF, IF_percent)
print "Overall Correct predictions: %i (%.2f%%)" % (total_correct, C_percent)
print "Overall Incorrect predictions: %i (%.2f%%)" % (total_incorrect, I_percent)

out_d = {}
out_d["results"] = {"Success": NS, "Fail": NF}
out_d["predictions"] = {"Correct_Success": CS, "Correct_Fail": CF,
        "Incorrect_Success": IS, "Incorrect_Fail": IF}
out_d["percentages"] = {"Correct_Success": CS_percent,
        "Correct_Fail": CF_percent, "Incorrect_Success": IS_percent,
        "Incorrect_Fail": IF_percent, "Overall_Correct": C_percent,
        "Overall_Incorrect": I_percent}

with open(opts.output, 'w') as f:
    json.dump(out_d, f, indent=4, separators=(',', ': '))
