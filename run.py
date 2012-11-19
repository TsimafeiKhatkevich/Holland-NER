#!/usr/bin/python
# vim: set file-encoding=utf-8:

import sys
import math
import itertools
import operator
import cPickle

import string

import maxent

from collections import defaultdict
from maxent import MaxentModel
from optparse import OptionParser

# |iterable| should yield lines.
def read_sentences(iterable):
    sentence = []
    for line in iterable:
        columns = line.rstrip().split()
        if len(columns) == 0 and len(sentence) > 0:
            yield sentence
            sentence = []
        if len(columns) > 0:
            sentence.append(columns)
    if len(sentence) > 0:
        yield sentence

# Computes (local) features for word at position |i| given that label for word
# at position |i - 1| is |previous_label|. You can pass any additional data
# via |data| argument.
MIN_WORD_FREQUENCY = 3
MIN_LABEL_FREQUENCY = 4

PREV_WORDS = dict({
#    "over": ["B-PER"],
#    "boven": ["B-LOC"],
    "tegen": ["B-LOC", "B_PER"],
    "op": ["B-LOC", "B-ORG"],
#    "voor": ["B-PER", "B-ORG"],
#    "tussen": ["B-PER"],
    "buiten": ["B-LOC"],
#    "door": ["B-PER", "B-ORG"],
    "tijdens": ["B-MISC"],
    "uit": ["B-LOC"],
#    "van": ["B-PER", "B-LOC", "B-ORG"],
    "in": ["B-LOC"],
    "aan": ["B-PER"],
    "met": ["B-PER", "B-ORG"],
    "volgens": ["B-PER"]
})

PROOF_MARKERS = ["minister", "dokter", "president", "koning", "prins", "directeur"]#"prinsesje"]
PROOF_MARKER_DIST = 4

def is_up(word):
    return word[0] in string.ascii_uppercase

def is_proof_marker(word):
    for marker in PROOF_MARKERS:
        if marker.endswith(word) or marker.startswith(word):
            return True
    return False

def compute_features(data, words, poses, i, previous_label):
    prev_word = words[i - 1] if i > 0 else ""
    word = words[i]

    marker_pos = data.get("proof_marker_pos", -1000)
    if is_proof_marker(word.lower()):
        marker_pos = i

    uppers, downs = 0, 0
    for letter in word:
        if letter in string.ascii_uppercase:
            uppers = uppers + 1
        else:
            downs = downs + 1

    # In test was words like 'hello-Vasya',
    # we try to find 'Vasya' and work with it
    was_defis = False
    if "-" in word:
        was_defis = True
        for w in word.split("-"):
            if len(w) > 0 and is_up(w):
                word = w
                break
        else:
            yield "was-labelled-as={0}".format("O")     

    # Check for first letter
    if not is_up(word):
        yield "was-labelled-as={0}".format("O")
    # ONLY IF UPPER LETTER
    else:
        # Check for part of speech
        if not poses[i] in ["V", "N", "Int", "Art", "Prep", "Adj", "Adv"]:
            yield "was-labelled-as={0}".format("O")

        # Check for words with different cases 'AvsdA'
        if uppers > 1 and downs > 0:
            yield "was-labelled-as={0}".format("I-MISC" if previous_label[0] == "B" else "B-MISC")

        if marker_pos + 1 == i:
            yield "was-labelled-as={0}".format("B-PER")

        if marker_pos + 2 == i and previous_label == "B-PER":
            yield "was-labelled-as={0}".format("I-PER")

        # For seases and towns
        if word.endswith("zee") or word.endswith("stad") or word.endswith("burg") or word.endswith("burgh"):
            yield "was-labelled-as={0}".format("I-LOC" if previous_label[0] == "B" else "B-LOC")

        if poses[i - 1] == "V" and previous_label == "O":
            yield "was-labelled-as={0}".format("B-PER")

        # Check for abbreviation
        if word.upper() == word:
            if not was_defis:
                yield "was-labelled-as={0}".format("I-ORG" if previous_label[0] == "B" else "B-ORG")
            else:
                yield "was-labelled-as={0}".format("I-MISC" if previous_label[0] == "B" else "B-MISC")

        if poses[i - 1] == "Art" and previous_label == "O":
            yield "was-labelled-as={0}".format("B-MISC")

        # Check previous word
        for (pr_w, labs) in PREV_WORDS.items():
            if not pr_w == prev_word.lower():
                continue
            for l in labs:
                only_o = False
                yield "was-labelled-as={0}".format(l)

        labels = data["labelled_words"].get(word, dict())
        labels = filter(lambda item: item[1] > MIN_LABEL_FREQUENCY, labels.items())

        for label in labels:
            yield "was-labelled-as={0}".format(label)

        if data["word_frequencies"].get(word, 0) >= MIN_WORD_FREQUENCY:
            yield "word-current={0}".format(word)

        # Condition on previous label.
        if previous_label != "O":
            yield "label-previous={0}".format(previous_label)

    data["proof_marker_pos"] = marker_pos


# |iterable| should yield sentences.
# |iterable| should support multiple passes.
def train_model(options, iterable):
    model = MaxentModel()
    data = {}

    data["feature_set"] = set()
    data["word_frequencies"] = defaultdict(long)
    # XXX(sandello): defaultdict(lambda: defaultdict(long)) would be
    # a better choice here (for |labelled_words|) but it could not be pickled.
    # C'est la vie.
    data["labelled_words"] = dict()

    print >>sys.stderr, "*** Training options are:"
    print >>sys.stderr, "   ", options

    print >>sys.stderr, "*** First pass: Computing statistics..."
    for n, sentence in enumerate(iterable):
        if (n % 1000) == 0:
            print >>sys.stderr, "   {0:6d} sentences...".format(n)
        for word, pos, label in sentence:
            data["word_frequencies"][word] += 1
            if label.startswith("B-") or label.startswith("I-"):
                if word in data["labelled_words"]:
                    data["labelled_words"][word][label] += 1
                else:
                    data["labelled_words"][word] = defaultdict(long)

    print >>sys.stderr, "*** Second pass: Collecting features..."
    model.begin_add_event()
    for n, sentence in enumerate(iterable):
        if (n % 1000) == 0:
            print >>sys.stderr, "   {0:6d} sentences...".format(n)
        words, poses, labels = map(list, zip(*sentence))
        for i in xrange(len(labels)):
            features = compute_features(data, words, poses, i, labels[i - 1] if i >= 1 else "^")
            features = list(features)
            model.add_event(features, labels[i])
            for feature in features:
                data["feature_set"].add(feature)
    model.end_add_event(options.cutoff)
    print >>sys.stderr, "*** Collected {0} features.".format(len(data["feature_set"]))

    print >>sys.stderr, "*** Training..."
    maxent.set_verbose(1)
    model.train(options.iterations, options.technique, options.gaussian)
    maxent.set_verbose(0)

    print >>sys.stderr, "*** Saving..."
    model.save(options.model + ".maxent")
    with open(options.model + ".data", "w") as handle:
        cPickle.dump(data, handle)

# |iterable| should yield sentences.
def eval_model(options, iterable):
    model = MaxentModel()
    data = {}

    print >>sys.stderr, "*** Loading..."
    model.load(options.model + ".maxent")
    with open(options.model + ".data", "r") as handle:
        data = cPickle.load(handle)

    print >>sys.stderr, "*** Evaluating..."
    for n, sentence in enumerate(iterable):
        if (n % 100) == 0:
            print >>sys.stderr, "   {0:6d} sentences...".format(n)
        words, poses = map(list, zip(*sentence))
        labels = eval_model_sentence(options, data, model, words, poses)

        for word, pos, label in zip(words, poses, labels):
            print label
        print

# This is a helper method for |eval_model_sentence| and, actually,
# an implementation of Viterbi algorithm.
def eval_model_sentence(options, data, model, words, poses):
    viterbi_layers = [ None for i in xrange(len(words)) ]
    viterbi_backpointers = [ None for i in xrange(len(words) + 1) ]

    # Compute first layer directly.
    viterbi_layers[0] = model.eval_all(list(compute_features(data, words, poses, 0, "^")))
    viterbi_layers[0] = dict( (k, math.log(v)) for k, v in viterbi_layers[0] )
    viterbi_backpointers[0] = dict( (k, None) for k, v in viterbi_layers[0].iteritems() )

    # Compute intermediate layers.
    for i in xrange(1, len(words)):
        viterbi_layers[i] = defaultdict(lambda: float("-inf"))
        viterbi_backpointers[i] = defaultdict(lambda: None)
        for prev_label, prev_logprob in viterbi_layers[i - 1].iteritems():
            features = compute_features(data, words, poses, i, prev_label)
            features = list(features)
            for label, prob in model.eval_all(features):
                logprob = math.log(prob)
                if prev_logprob + logprob > viterbi_layers[i][label]:
                    viterbi_layers[i][label] = prev_logprob + logprob
                    viterbi_backpointers[i][label] = prev_label

    # Most probable endpoint.
    max_logprob = float("-inf")
    max_label = None
    for label, logprob in viterbi_layers[len(words) - 1].iteritems():
        if logprob > max_logprob:
            max_logprob = logprob
            max_label = label

    # Most probable sequence.
    path = []
    label = max_label
    for i in reversed(xrange(len(words))):
        path.insert(0, label)
        label = viterbi_backpointers[i][label]

    return path

################################################################################

def main():
    parser = OptionParser("A sample MEMM model for NER")
    parser.add_option("-T", "--train", action="store_true", dest="train",
        help="Do the training, if specified; do the evaluation otherwise")
    parser.add_option("-f", "--file", type="string", dest="filename",
        metavar="FILE", help="File with the training data")
    parser.add_option("-m", "--model", type="string", dest="model",
        metavar="FILE", help="File with the model")
    parser.add_option("-c", "--cutoff", type="int", default=5, dest="cutoff",
        metavar="C", help="Event frequency cutoff during training")
    parser.add_option("-i", "--iterations", type="int", default=100, dest="iterations",
        metavar="N", help="Number of training iterations")
    parser.add_option("-g", "--gaussian", type="float", default=0.0, dest="gaussian",
        metavar="G", help="Gaussian smoothing penalty (sigma)")
    parser.add_option("-t", "--technique", type="string", default="gis", dest="technique",
        metavar="T", help="Training algorithm (either 'gis' or 'lbfgs')")
    (options, args) = parser.parse_args()

    if not options.filename:
        parser.print_help()
        sys.exit(1)

    with open(options.filename, "r") as handle:
        data = list(read_sentences(handle))

    if options.train:
        print >>sys.stderr, "*** Training model..."
        train_model(options, data)
    else:
        print >>sys.stderr, "*** Evaluating model..."
        eval_model(options, data)

    print >>sys.stderr, "*** Done!"

if __name__ == "__main__":
    main()

