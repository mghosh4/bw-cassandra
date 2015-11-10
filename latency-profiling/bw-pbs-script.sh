#!/bin/bash
#PBS -l nodes=100:ppn=32:xe
#PBS -l walltime=01:00:00
#PBS -l gres=ccm
##PBS -j oe
##PBS -o /u/sciteam/ghosh1/scratch/$PBS_JOBID.out
#PBS -e /u/sciteam/ghosh1/scratch/log/$PBS_JOBID.err
#PBS -o /u/sciteam/ghosh1/scratch/log/$PBS_JOBID.out
#PBS -m bea
#PBS -M ghosh14@illinois.edu


source /opt/modules/default/init/bash
module list

#. /opt/modules/default/init/bash
module load ccm

export APRUN_XFER_LIMITS=1

cd /projects/sciteam/jsb/ghosh1/bw-cassandra/latency-profiling
ccmrun sh bw-ccmrun.sh
