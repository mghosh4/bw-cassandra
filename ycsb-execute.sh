#!/bin/bash
# DATE       AUTHOR      COMMENT
# ---------- ----------- -----------------------------------------------------
# 2015-03-07 Yosub Shin  Initial Version

for i in "$@"
do
case $i in
    --ycsb_path=*)
    YCSB_PATH="${i#*=}"
    shift
    ;;
    --base_path=*)
    BASE_PATH="${i#*=}"
    shift
    ;;
    --throughput=*)
    THROUGHPUT="${i#*=}"
    shift
    ;;
    --host=*)
    HOST="${i#*=}"
    shift
    ;;
    --profile=*)
    PROFILE="${i#*=}"
    shift
    ;;
    --delay_in_millisec=*)
    DELAY_IN_MILLISEC="${i#*=}"
    shift
    ;;
    *)
            # unknown option
    ;;
esac
done

if [ "emulab" = "$PROFILE" ]; then
ulimit -n 32768
fi


# Execute YCSB Workload
${YCSB_PATH}/bin/ycsb run cassandra-cql -s -target ${THROUGHPUT} -P ${BASE_PATH}/workload.txt -p warmupexecutiontime=${DELAY_IN_MILLISEC} > ${BASE_PATH}/execution-output-${HOST}.txt
