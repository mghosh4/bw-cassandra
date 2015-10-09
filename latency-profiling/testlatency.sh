#!/bin/bash

mkdir -p $1
NUM_PINGS=30

filename=`hostname`
filename="$filename".log

nodenames=$(echo $3 | tr "," "\n")

for name in $nodenames
do
	if [ `hostname` != $name ]; then
		echo "From" $filename "pinging" $name
		ping -s $2 -c $NUM_PINGS $name >> $1/$filename
	fi
done
