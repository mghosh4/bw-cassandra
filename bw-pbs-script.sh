#!/bin/bash
#PBS -l nodes=20:ppn=32:xe
#PBS -l walltime=02:00:00
#PBS -l gres=ccm
#PBS -j oe
#PBS -o /u/sciteam/shin1/scratch/$PBS_JOBID.out
#PBS -m bea
#PBS -M shin14@illinois.edu

. /opt/modules/default/init/bash
module load ccm

export APRUN_XFER_LIMITS=1

cd /u/sciteam/shin1/scratch/bw-cassandra
ccmrun sh bw-ccmrun.sh
