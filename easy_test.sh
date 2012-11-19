#!/usr/bin/env bash

do_not_test=0
evaluated="data/dutch.train.evaluated.txt"
results="data/dutch.train.results.txt" 
clean="data/dutch.train.clean.txt" 
for var in "$@"
do
    case "$var" in
    -t*) do_not_test=1
        ;;
    esac
done

if (( $do_not_test == 0 ))
then
    ./run.sh -f data/dutch.train.clean.txt -c 5 -i 200 -g 3.5 -m dutch > $evaluated
fi

./get_info.py $evaluated $results $clean 

