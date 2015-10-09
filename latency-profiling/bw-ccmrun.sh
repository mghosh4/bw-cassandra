#!/bin/bash

python coordinator.py bw ${PBS_JOBID} 2>&1 | tee /u/sciteam/shin1/scratch/log/bw-cassandra-log-${PBS_JOBID}.txt
