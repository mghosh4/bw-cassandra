#!/bin/bash
#PBS -j oe
#PBS -l nodes=20:ppn=32:xe
#PBS -l walltime=02:00:00
#PBS -l gres=ccm

export APRUN_XFER_LIMITS=1 

module load ccm

cd /u/sciteam/shin1/scratch/bw-cassandra
ccmrun sh bw-ccmrun.sh
