#!/bin/bash
#PBS -j oe
#PBS -l nodes=20:ppn=32:xe
#PBS -l walltime=02:00:00
#PBS -l gres=ccm

APRUN_XFER_LIMITS=1 

module add ccm

cd /u/sciteam/shin1/scratch
ccmrun sh bw-ccmrun.sh
