#!/usr/bin/env bash
do_train=0
do_test=0
do_viz=0
do_eval=0
evaluated="data/dutch.train.evaluated.txt"
testing="data/dutch.test.txt"
training="data/dutch.train.txt"
results="data/dutch.train.results.txt" 
clean="data/dutch.train.clean.txt" 
senme="data/sendme.txt"
for var in "$@"
do
    case "$var" in
    -t*) do_test=1
        ;;
    -T*) do_train=1
        ;;
    -v*) do_viz=1
        ;;
    -e*) do_eval=1
    esac
done

if (( $do_train == 1 ))
then
    ./run.sh -f $training -c 5 -i 200 -g 3.5 -m dutch -T
fi

if (( $do_eval == 1 ))
then
    ./run.sh -f $testing -c 5 -i 200 -g 3.5 -m dutch > $sendme
fi

if (( $do_test == 1 ))
then
    ./run.sh -f $clean -c 5 -i 200 -g 3.5 -m dutch > $evaluated
fi

if (( $do_viz == 1 ))
then
    ./get_info.py $evaluated $results $clean 
fi

