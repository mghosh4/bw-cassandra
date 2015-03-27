#!/bin/bash
# DATE       AUTHOR      COMMENT
# ---------- ----------- -----------------------------------------------------
# 2015-03-07 Yosub Shin  Initial Version

for i in "$@"
do
case $i in
    --cassandra_path=*)
    CASSANDRA_PATH="${i#*=}"
    shift
    ;;
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
    --num_records=*)
    NUM_RECORDS="${i#*=}"
    shift
    ;;
    --workload=*)
    WORKLOAD="${i#*=}"
    shift
    ;;
    --replication_factor=*)
    REPLICATION_FACTOR="${i#*=}"
    shift
    ;;
    --seed_host=*)
    SEED_HOST="${i#*=}"
    shift
    ;;
    --hosts=*)
    HOSTS="${i#*=}"
    shift
    ;;
    *)
            # unknown option
    ;;
esac
done

cat > /tmp/cql_input.txt <<EOF
create keyspace ycsb WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor': ${REPLICATION_FACTOR} };
create table ycsb.usertable (
    y_id varchar primary key,
    field0 blob,
    field1 blob,
    field2 blob,
    field3 blob,
    field4 blob,
    field5 blob,
    field6 blob,
    field7 blob,
    field8 blob,
    field9 blob);
EOF

# Setup keyspace and column family in Cassandra for YCSB workload
${CASSANDRA_PATH}/bin/cqlsh --file=/tmp/cql_input.txt ${SEED_HOST}

# Create output directory if not exists
if [ ! -f ${BASE_PATH} ]; then
    mkdir ${BASE_PATH}
fi

# Create YCSB workload file
cat > ${BASE_PATH}/workload.txt <<EOF
recordcount=${NUM_RECORDS}

# Run YCSB for 60 seconds
operationcount= $(( 60 * $THROUGHPUT ))
maxexecutiontime=60
workload=com.yahoo.ycsb.workloads.CoreWorkload

readallfields=true

readproportion=0.95
updateproportion=0.05
scanproportion=0
insertproportion=0

requestdistribution=${WORKLOAD}

threadcount=150

# For CQL client
hosts=${HOSTS}
port=9042
columnfamily=usertable

histogram.buckets=10000

# number of operations in warmup phase, if zero then don't warmup(default: 0)
warmupoperationcount=100000
# execution time of warmup phase in milliseconds, if zero then don't warmup (default: 0)
warmupexecutiontime=30000

EOF

# Load YCSB Workload
${YCSB_PATH}/bin/ycsb load cassandra-cql -s -P ${BASE_PATH}/workload.txt > ${BASE_PATH}/load-output.txt
