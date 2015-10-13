#!/bin/bash

JOBID=`date +%m-%d-%H%M`
mkdir -p ~/log

python coordinator.py gcloud ${JOBID} 2>&1 | tee ~/log/bw-cassandra-log-${JOBID}.txt
