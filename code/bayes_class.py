import cPickle as pickle
import json
from copy import deepcopy

"""
A Bayesian classifier to ingest authentication logs, predict success/failure
and tabulate results and stats about the logs
"""

class AuthClassifier:
    """
    Class to read in authentication logs and predict whether each event
    will be a success or failure.
    Processes the authentication log in chronological chunks.
    Computes likelihood ratio by exact enumeration of 'recent' events,
    where 'recent' is taken to mean events in the current and/or previous
    chunk.
    """
    def __init__(self, prior_ratio, predict=True, full_tabulate=False):
        self.prior_ratio = prior_ratio
        # Flags to control behavior
        self.predict = predict
        self.full_tabulate = full_tabulate
        # Counts of total Successes and Failures
        # In current/previous auth chunks
        self.NS_curr = 0
        self.NF_curr = 0
        self.NS_prev = 0
        self.NF_prev = 0
        # Dictionaries to store counts of S/F by user-protocol keys
        self.S_curr_d = {}
        self.F_curr_d = {}
        self.S_prev_d = {}
        self.F_prev_d = {}
        # Arrays to hold various outputs
        self.results = []
        self.predictions = []
        self.Bayes_arr = []
        self.S_arr = []
        self.F_arr = []

    def parse_line(self, line):
        """
        Each line is a CSV where the first column is an integer time,
        the last column is either Success or Fail, and the columns in between
        all describe the source/dest user, computer and domain and the type of
        authentication action attempted. We concatenate all these middle columns
        into a single 'user-protocol' (UP) key.
        """
        ls = line.split(",")
        T = ls[0]
        UP = ",".join(ls[1:-1]) # user-protocol key
        R = ls[-1][:1] # Just need 1st char. S/F from last column
        assert (R=="S" or R=="F")
        return T, UP, R

    def likelihood_ratio(self, key):
        """
        Compute the likelihood ratio p(key|F) / p(key|S).
        p(key|r) is estimated by the fraction of recent events with same result
        that had the same key.
        """
        # Likelihood of key, given Success
        like_S = 0.
        try:
            like_S += self.S_curr_d[key]
        except KeyError:
            pass
        try:
            like_S += self.S_prev_d[key]
        except KeyError:
            pass
        # p(key|S) = recent successes of key / total recent successes
        like_S /= (self.NS_curr + self.NS_prev)

        # Likelihood of key, given Failure
        like_F = 0.
        try:
            like_F += self.F_curr_d[key]
        except KeyError:
            pass
        try:
            like_F += self.F_prev_d[key]
        except KeyError:
            pass
        # p(key|F) = recent failures of key / total recent failures
        like_F /= (self.NF_curr + self.NF_prev)

        if like_S==0. and like_F== 0.:
            # Data uninformative, set LR=1 so posterior = prior
            LR = 1.
        elif like_S==0.:
            # Recent failures, no successes. Don't want to divide by zero
            # So set likelihood to arbitrary large value to predict Fail
            LR = 1.e9
        else:
            LR = like_F / like_S
        return LR

    def process_line(self, line):
        """
        Perform all steps needed to process a single event in auth log:
            1. Parse the line into time, user-protocol key, result
            2. Compute Bayes factor and predict Success/Fail
            3. Update dicts/counts used in likelihood computation
            4. Tabulate results
        """
        T, key, R = self.parse_line(line)
        self.results.append(R)
        if self.predict:
            LR = self.likelihood_ratio(key)
            # Bayes factor = likelihood ratio * prior ratio
            B = LR * self.prior_ratio
            # When B == 1., equal odds of S/F, we arbitrarily predict S
            if B <= 1.:
                prediction="S"
            else:
                prediction="F"
            self.predictions.append(prediction)
            self.Bayes_arr.append(B)
        if R=="S":
            self.NS_curr += 1
            try:
                self.S_curr_d[key] += 1
            except KeyError: # 1st recent success by key, create new entry
                self.S_curr_d[key] = 1
        elif R=="F":
            self.NF_curr += 1
            try:
                self.F_curr_d[key] += 1
            except KeyError: # 1st recent failure by key, create new entry
                self.F_curr_d[key] = 1
        else:
            raise ValueError("Invalid result string %s" % R)
        if self.full_tabulate:
            if R=="S":
                self.S_arr.append([T, key, R])
            elif R=="F":
                self.F_arr.append([T, key, R])
            else:
                raise ValueError("Invalid result string %s" % R)

    def process_chunk(self, fname):
        """
        Apply process_line to every line of auth log chunk referenced by
        FileHandler fptr.
        """
        with open(fname, 'r') as f:
            for line in f:
                self.process_line(line)

    def pickle_current_counts(self, fname):
        """
        Dump information about current chunk S/F counts to a pickle file.
        """
        with open(fname, 'wb') as f:
            data = (self.NS_curr, self.NF_curr, self.S_curr_d, self.F_curr_d)
            pickle.dump(data, f)

    def previous_counts_from_pickle(self, fname):
        """
        Load information about previous chunk S/F counts from a pickle file.
        """
        with open(fname, 'rb') as f:
            self.NS_prev, self.NF_prev, self.S_prev_d, self.F_prev_d = pickle.load(f)

    def pickle_current_arrays(self, fname):
        """
        Dump to pickle the auth events parsed in current chunk as arrays of
        [time, UP key, result] separated into an array of all successes,
        followed by an array of all failures
        """
        with open(fname, 'wb') as f:
            data = (self.S_arr, self.F_arr)
            pickle.dump(data, f)

    def tally_predictions(self):
        """
        Return a 4-tuple of integers:
            Correct_Success (guessed Success, was Success)
            Correct_Fail (guessed Fail, was Fail)
            Incorrect_Success (guessed Success, was Fail)
            Incorrect_Fail (guessed Fail, was Success)
        """
        CS = 0
        CF = 0
        IS = 0
        IF = 0
        assert len(self.results)==len(self.predictions)
        for i in range(len(self.results)):
            if self.predictions[i]==self.results[i]=='S':
                CS += 1
            elif self.predictions[i]==self.results[i]=='F':
                CF += 1
            elif  self.predictions[i]=='S' and self.results[i]=='F':
                IS += 1
            elif  self.predictions[i]=='F' and self.results[i]=='S':
                IF += 1
        return CS, CF, IS, IF

    def write_summary(self, fname):
        """
        Summarize results from the current chunk. Write to JSON file 'fname'.
        Write JSON output as follows:
        results:
            Success (number in this chunk)
            Fail (number in this chunk)
        predictions:
            Correct_Success (guessed Success, was Success)
            Correct_Fail (guessed Fail, was Fail)
            Incorrect_Success (guessed Success, was Fail)
            Incorrect_Fail (guessed Fail, was Success)
        """
        out_d = {}
        out_d["results"] = {"Success": self.NS_curr, "Fail": self.NF_curr}
        if self.predict:
            CS, CF, IS, IF = self.tally_predictions()
            tmp_d = {}
            tmp_d["Correct_Success"] = CS
            tmp_d["Correct_Fail"] = CF
            tmp_d["Incorrect_Success"] = IS
            tmp_d["Incorrect_Fail"] = IF
            out_d["predictions"] = tmp_d
        with open(fname, 'w') as f:
            json.dump(out_d, f, indent=4, separators=(',', ': '))

    def prior_from_summary_files(self, chunk_number, summary_dir):
        """
        Read in all summary JSON files from chunks before 'chunk_number'
        found in 'summary_dir'. Sum up Fails and Successes across all chunks,
        take the ratio NF / NS to get prior ratio.
        """
        prior_NS = 0
        prior_NF = 0
        for chunk in range(0,opts.start_chunk):
            summary_name = str("summary_x%05d.json" % chunk)
            fname = os.path.join(opts.summary_directory, summary_name)
            with open(fname, 'r') as f:
                summary_d = json.load(f)
            prior_NS = summary_d["results"]["Success"]
            prior_NF = summary_d["results"]["Fail"]
        prior_ratio = float(prior_NF / prior_NS)
        return prior_ratio

    def reset(self, prior_ratio):
        """
        Reset counts and arrays to prepare to process a new chunk.
        """
        self.prior_ratio = prior_ratio
        self.NS_prev = self.NS_curr
        self.NF_prev = self.NF_curr
        self.NS_curr = 0
        self.NF_curr = 0
        self.S_prev_d = deepcopy(self.S_curr_d)
        self.F_prev_d = deepcopy(self.F_curr_d)
        self.S_curr_d = {}
        self.F_curr_d = {}
        self.results = []
        self.predictions = []
        self.Bayes_arr = []
        self.S_arr = []
        self.F_arr = []

    def reset_from_pickle(self, prior_ratio, fname):
        """
        Reset counts and arrays to prepare to process a new chunk.
        Reads in previous counts from prev chunk's pickle file fname
        """
        self.prior_ratio = prior_ratio
        self.NS_curr = 0
        self.NF_curr = 0
        self.S_curr_d = {}
        self.F_curr_d = {}
        self.NS_prev, self.NF_prev, self.S_prev_d, self.F_prev_d = self.previous_counts_from_pickle(fname)
        self.results = []
        self.predictions = []
        self.Bayes_arr = []
        self.S_arr = []
        self.F_arr = []


