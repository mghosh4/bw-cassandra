#!/bin/bash

mkdir -p $1
NUM_PINGS=30

filename=`hostname`
filename="$filename".log

nodenames=$3

for name in $nodenames
do
	if [ `hostname` != $name ]; then
		ping -s $2 -c $NUM_PINGS $name >> $1/$filename
	fi
done
