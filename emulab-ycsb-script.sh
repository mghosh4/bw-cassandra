#!/bin/bash
# DATE       AUTHOR      COMMENT
# ---------- ----------- -----------------------------------------------------
# 2015-03-07 Yosub Shin  Initial Version

CASSANDRA_HOME=/opt/cassandra
YOSUB_PERSONAL_HOST=http://104.236.110.182
YCSB_HOME=/tmp/YCSB

for i in "$@"
do
case $i in
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
${CASSANDRA_HOME}/bin/cqlsh --file=/tmp/cql_input.txt node-0

# Download and extract YCSB binary
if [ ! -f /tmp/ycsb-cassandra.tar.gz ]; then
    wget --directory-prefix=/tmp ${YOSUB_PERSONAL_HOST}/ycsb-cassandra.tar.gz    
fi
tar -xzf /tmp/ycsb-cassandra.tar.gz -C /tmp

# Create output directory if not exists
if [ ! -f ${BASE_PATH} ]; then
    mkdir ${BASE_PATH}
fi

# Create YCSB workload file
cat > ${BASE_PATH}/workload.txt <<EOF
recordcount=${NUM_RECORDS}

# Run YCSB for 60 seconds
operationcount= $(( 60 * $THROUGHPUT ))
workload=com.yahoo.ycsb.workloads.CoreWorkload

readallfields=true

readproportion=0.95
updateproportion=0.05
scanproportion=0
insertproportion=0

requestdistribution=${WORKLOAD}

threadcount=30

# For CQL client
hosts=node-0
port=9042
columnfamily=usertable

EOF

# Load YCSB Workload
${YCSB_HOME}/bin/ycsb load cassandra-cql -s -P ${BASE_PATH}/workload.txt

# Execute YCSB Workload
# -s: report status every 10 seconds to stderr
# -target: throughput(ops/s)
# -P: workload file
${YCSB_HOME}/bin/ycsb run cassandra-cql -s -target ${THROUGHPUT} -P ${BASE_PATH}/workload.txt > ${BASE_PATH}/execution-output.txt
