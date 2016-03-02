# Bayesian Classifier for authentication data

## Overview

This project contains, code, results, and a description of a Bayesian
method to predict whether authentication attempts will succeed or fail
based on exact enumeration over recent authentication attempts.

The data and a description of the format can be found at:
http://csr.lanl.gov/data/cyber1/

It consists of roughly one billion CSV lines of authentication logs
with the time, information about the users and authentication action,
and whether the authentication attempt succeeded or failed.

The main code lives in `code/bayes_class.py` and defines an `AuthClassifier`
class which parses the auth logs and performs computations.

This directory also contains four executables:
1. `train.py`
2. `study_chunk.py`
3. `run_classifier.py`
4. `summarize.py`

The latter two accept arguments to control their behavior, and '-h' or '--help'
will give a help message.

## How to use

Note this is a prototype code, so I did not bother with a `setup.py` script.
All executables should be run in place from the `code/` directory.

The following steps will reproduce all results:
1. `cd data/input_data`
2. `curl -o auth.txt.gz http://csr.lanl.gov/data/cyber1/auth.txt.gz`
3. `gunzip -c auth.txt.gz | split -d -a 5 -l 1000000`
4. `cd ../../code/`
5. `./train.py`
6. `./study_chunk.py`
7. `./run_classifier.py -s 1 -e 1051`
8. `./summarize.py`


## Notes

This is a prototype code to demonstrate the basic method works. As such, I have
not bothered to make it robust as possible.

No `setup.py` script is provided, instead the executables are expected to be
run from the code directory.

Additionally, it is assumed all inputs files are named with a x followed by a 5-digit integer, i.e. x00000, x00001, ..., x01051.


### Getting the data

This is covered by Steps 1-3 above. Of course the file auth.txt.gz
can be obtained by many means other than curl.

Note some versions of `split` do not accept the `-d` or `--numeric-suffixes`
option, and instead will use alphabetic suffixes, producing names like `xaac`.
In this case, you may need to split the files by some other means. 

You could split with alphabetic suffixes and write a little wrapper to
treat alphabetic suffixes as base-26 numbers, where the
letters have values 0-25, and map this to a base-10 number.

e.g. `abc = (0 * 26**2) + (1 * 26**1) + (2 * 26**0) = 28`

Then you can split the files and rename them according to the mapping.

### Training the classifier

Step 5 just tallies Success and Failures in the first chunk of 1 million auth
events without trying to predict the outcome. This is used to set the prior
probabilities used to classify the subsequent chunks.

Step 6 Merely produces a plot of the Success/Fail rates in this first chunk
and prints some other summary information about the chunk to stdout.

Note these two scripts hardcode the location of the first input chunk,
assumed to be `sqrrl_homework/data/input_data/x00000`. If you store it
elsewhere you will have to edit these scripts with a trivial change.


### Running the classifier

Step 7 will run the classifier over the entire dataset. Note this will take
roughly two hours on a modest laptop. You may wish to run over a smaller subset
first to test it out, e.g.

`cd sqrrl_homework/code`
`./run_classifier.py -s 1 -e 5`

will analyze the first 5 chunks of data. If you store the data elsewhere,
you can pass other arguments so it will find the data.

The main output is a JSON file summarizing the performance on that chunk,
by default `sqrrl_homework/data/summary_data/xN.json` for chunk N.

It will also produced pickled output that the code uses internally to
`sqrrl_homework/data/intermediate_data`.

Step 8 merely parses all of these JSON outputs and writes final, cumulative
performance stats to both stdout and an output JSON file, by default
`sqrrl_homework/data/summary_data/final_summary.json`

## Documentation

The `doc/` directory contains a brief writeup describing the classification
method and the results.
