#!/bin/bash

export JAVA_HOME="/projects/sciteam/jsb/shin1/jdk1.7.0_65"

python coordinator.py bw ${PBS_JOBID} 2>&1 | tee /u/sciteam/shin1/scratch/log/bw-cassandra-log-${PBS_JOBID}.txt
