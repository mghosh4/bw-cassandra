#!/bin/bash
#TODO: Use the path variables defined in the init file

export JAVA_HOME="/projects/sciteam/jsb/ghosh1/jdk1.7.0_65"

python coordinator.py bw ${PBS_JOBID} 2>&1 | tee /u/sciteam/ghosh1/scratch/log/bw-cassandra-log-${PBS_JOBID}.txt
