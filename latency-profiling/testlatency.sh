#!/bin/bash

mkdir -p $1
NUM_PINGS=30

filename=`hostname`
filename="$filename".log

nodenames=$3

for name in $nodenames
do
	echo "For " $name
	if [ `hostname` != $name ]; then
		echo "ping" $name
		ping -s $2 -c $NUM_PINGS $name >> $1/$filename
	fi
done
