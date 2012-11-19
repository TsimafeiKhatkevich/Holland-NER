#!/usr/bin/env bash

./run.sh -f data/dutch.train.clean.txt -c 5 -i 200 -g 3.5 -m dutch > data/dutch.train.evaluated.txt

./get_info.py "data/dutch.train.evaluated.txt" "data/dutch.train.results.txt" "data/dutch.train.clean.txt"

