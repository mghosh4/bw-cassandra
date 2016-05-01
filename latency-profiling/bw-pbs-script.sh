#!/bin/bash
#PBS -l nodes=96:ppn=32:xe
#PBS -l walltime=02:00:00
#PBS -l geometry=4x4x3
##PBS -j oe
##PBS -o /u/sciteam/ghosh1/scratch/$PBS_JOBID.out
#PBS -e /u/sciteam/ghosh1/scratch/log/$PBS_JOBID.err
#PBS -o /u/sciteam/ghosh1/scratch/log/$PBS_JOBID.out
#PBS -m bea
#PBS -M ghosh1@illinois.edu


source /opt/modules/default/init/bash
echo $PBS_JOBID
#module list

#. /opt/modules/default/init/bash
#module load ccm

export APRUN_XFER_LIMITS=1

cd /projects/sciteam/jsb/ghosh1/bw-cassandra/latency-profiling
aprun -n 96 -N 1 testlatency.sh
