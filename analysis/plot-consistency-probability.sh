#!/bin/bash

for i in "$@"
do
case $i in
    --output_path=*)
    OUTPUT_PATH="${i#*=}"
    shift
    ;;
    --bw=*)
    BW="${i#*=}"
    shift
    ;;
    --emulab=*)
    EMULAB="${i#*=}"
    shift
    ;;
    *)
            # unknown option
    ;;
esac
done

gnuplot << EOF
set terminal pngcairo font 'Times,20' linewidth 2 size 15in,9in 
set output "${OUTPUT_PATH}"

set xlabel "Time after write (ms)"
set ylabel "Probability of consistent read"
set style line 1 lt rgb "#A00000" pt 1 pi 10 lw 2 ps 1.5
set style line 2 lt rgb "#00A000" pt 7 pi 10 lw 2 ps 1.5
set style line 3 lt rgb "#5060D0" pt 2 pi 10 lw 2 ps 1.5
set style line 4 lt rgb "#F25900" pt 9 pi 10 lw 2 ps 1.5
set style line 5 lt rgb "#ED0CCB" pt 5 pi 10 lw 2 ps 1.5
set   autoscale                        # scale axes automatically
# set logscale x
set xtic auto                          # set xtics automatically
set ytic auto                          # set ytics automatically
# set yrange [0:50]
# set xrange [0.8:200]
set key right bottom

set datafile separator ","

plot    "${BW}" using 1:2 title 'bw' with linespoints ls 2, \
    	"${EMULAB}" using 1:2 title 'emulab' with linespoints ls 3

EOF
