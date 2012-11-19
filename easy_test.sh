#!/usr/bin/env bash
do_train=0
do_test=0
do_viz=0
evaluated="data/dutch.train.evaluated.txt"
results="data/dutch.train.results.txt" 
clean="data/dutch.train.clean.txt" 
for var in "$@"
do
    case "$var" in
    -t*) do_test=1
        ;;
    -T*) do_train=1
        ;;
    -v*) do_viz=1
        ;;
    esac
done

if (( $do_train == 1 ))
then
    ./run.sh -f data/dutch.train.txt -c 5 -i 200 -g 3.5 -m dutch -T
fi

if (( $do_test == 1 ))
then
    ./run.sh -f data/dutch.train.clean.txt -c 5 -i 200 -g 3.5 -m dutch > $evaluated
fi

if (( $do_viz == 1 ))
then
    ./get_info.py $evaluated $results $clean 
fi

