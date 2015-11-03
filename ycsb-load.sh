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
    --num_threads=*)
    NUM_THREADS="${i#*=}"
    shift
    ;;
    --read_consistency=*)
    READ_CONSISTENCY="${i#*=}"
    shift
    ;;
    --write_consistency=*)
    WRITE_CONSISTENCY="${i#*=}"
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

sleep 10

# Create output directory if not exists
if [ ! -f ${BASE_PATH} ]; then
    mkdir -p ${BASE_PATH}
fi

# Create YCSB workload file
cat > ${BASE_PATH}/workload.txt <<EOF
recordcount=${NUM_RECORDS}

# Run YCSB for 100 seconds
# Safe limit of operation count to accomodate for running 300 seconds with 1M ops/s
operationcount=1000
maxexecutiontime=60
workload=com.yahoo.ycsb.workloads.CoreWorkload

readallfields=true

readproportion=0
updateproportion=0
scanproportion=0
insertproportion=1

requestdistribution=${WORKLOAD}

threadcount=${NUM_THREADS}

# For CQL client
hosts=${HOSTS}
port=9042
columnfamily=usertable

histogram.buckets=1000000

cassandra.writeconsistencylevel=${WRITE_CONSISTENCY}
cassandra.readconsistencylevel=${READ_CONSISTENCY}

EOF

# Load YCSB Workload
${YCSB_PATH}/bin/ycsb load cassandra-cql -s -P ${BASE_PATH}/workload.txt -p maxexecutiontime=600 -p threadcount=128 -p operationcount=300000000> ${BASE_PATH}/load-output.txt

cat > /tmp/cql_tracing.txt <<EOF
TRACING ON
EOF

# Setup keyspace and column family in Cassandra for YCSB workload
${CASSANDRA_PATH}/bin/cqlsh --file=/tmp/cql_tracing.txt ${SEED_HOST}

sleep 10
