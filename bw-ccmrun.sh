#!/bin/bash

cd /u/sciteam/shin1/scratch/bw-cassandra
python coordinator.py bw 2>&1 | tee /u/sciteam/shin1/scratch/bw-cassandra-log.txt
