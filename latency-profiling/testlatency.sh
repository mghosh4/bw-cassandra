#!/bin/bash

resultpath="/u/sciteam/ghosh1/scratch/result/16384"
NUM_PINGS=30

filename=`hostname`
latencyfilename="$filename"_latency.log

nodenames=$(cat /projects/sciteam/jsb/ghosh1/result/hostlist | awk '{system("rca-helper -x "$1)}')

for name in $nodenames
do
	if [ `hostname` != $name ]; then
		ping -i 0.2 -s 16384 -c $NUM_PINGS $name >> $resultpath/$latencyfilename
	fi
done
