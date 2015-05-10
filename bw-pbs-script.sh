#!/bin/bash
#PBS -l nodes=21:ppn=32:xe
#PBS -l walltime=5:00:00
#PBS -l gres=ccm
##PBS -j oe
##PBS -o /u/sciteam/shin1/scratch/$PBS_JOBID.out
#PBS -e /u/sciteam/shin1/scratch/log/$PBS_JOBID.err
#PBS -o /u/sciteam/shin1/scratch/log/$PBS_JOBID.out
#PBS -m bea
#PBS -M shin14@illinois.edu


source /opt/modules/default/init/bash
module list

#. /opt/modules/default/init/bash
module load ccm

export APRUN_XFER_LIMITS=1

cd /projects/sciteam/jsb/shin1/bw-cassandra
ccmrun sh bw-ccmrun.sh
