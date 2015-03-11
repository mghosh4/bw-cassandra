#!/bin/bash
# DATE       AUTHOR      COMMENT
# ---------- ----------- -----------------------------------------------------
# 2014-08-22 Yosub       Initial version
# 2014-09-10 Yosub       Inspect Cassandra's running status after deploy

for i in "$@"
do
case $i in
    --basedir=*)
    REMOTE_BASE_DIR="${i#*=}"
    shift
    ;;
    --cluster_size=*)
    CLUSTER_SIZE="${i#*=}"
    shift
    ;;
    --active_cluster_size=*)
    ACTIVE_CLUSTER_SIZE="${i#*=}"
    shift
    ;;
    --src_dir_name=*)
    CASSANDRA_SRC_DIR_NAME="${i#*=}"
    shift
    ;;
    *)
    # unknown option
    ;;
esac
done

CASSANDRA_SRC_TAR_FILE=${CASSANDRA_SRC_DIR_NAME}.tar.gz
CASSANDRA_HOME=/opt/cassandra
REMOTE_SCRIPT_DIR=${REMOTE_BASE_DIR}
REMOTE_REDEPLOY_SCRIPT=${REMOTE_SCRIPT_DIR}/redeploy-node-script.sh

# Set JAVA_HOME
export JAVA_HOME=/usr/lib/jvm/jdk1.7.0

# Delete existing Cassandra directory
rm -rf ${REMOTE_BASE_DIR}/${CASSANDRA_SRC_DIR_NAME}

# Extract Cassandra
tar -xzf ${REMOTE_BASE_DIR}/${CASSANDRA_SRC_TAR_FILE} -C ${REMOTE_BASE_DIR}

# Invoke redeploy script for each node, parallelize after node-0
for (( i=0; i < CLUSTER_SIZE; i++))
do
if [ $i == 0 ]; then
    echo "## Invoking redeploy script on node-$i as the primary seed node"
    ssh -o "StrictHostKeyChecking no" node-$i "sudo $REMOTE_REDEPLOY_SCRIPT --basedir=${REMOTE_BASE_DIR} --src_dir_name=${CASSANDRA_SRC_DIR_NAME} --node_address=node-$i --seed_address=node-0"
    echo "## Finished invoking redeploy script on node-$i"
elif [ "$i" -lt "$ACTIVE_CLUSTER_SIZE" ]; then
    (
    echo "## Invoking redeploy script on node-$i with seed being node-0"
    ssh -o "StrictHostKeyChecking no" node-$i "sudo $REMOTE_REDEPLOY_SCRIPT --basedir=${REMOTE_BASE_DIR} --src_dir_name=${CASSANDRA_SRC_DIR_NAME} --node_address=node-$i --seed_address=node-0"
    echo "## Finished invoking redeploy script on node-$i"
    ) &
elif [ "$i" -eq "$ACTIVE_CLUSTER_SIZE" ]; then
# The primary among unused nodes
    echo "## Invoking redeploy script on node-$i as the secondary seed node"
    ssh -o "StrictHostKeyChecking no" node-$i "sudo $REMOTE_REDEPLOY_SCRIPT --basedir=${REMOTE_BASE_DIR} --src_dir_name=${CASSANDRA_SRC_DIR_NAME} --node_address=node-$i --seed_address=node-${ACTIVE_CLUSTER_SIZE}"
    echo "## Finished invoking redeploy script on node-$i"
else
# Unused nodes
    (
    echo "## Invoking redeploy script on node-$i with seed being node-${ACTIVE_CLUSTER_SIZE}"
    ssh -o "StrictHostKeyChecking no" node-$i "sudo $REMOTE_REDEPLOY_SCRIPT --basedir=${REMOTE_BASE_DIR} --src_dir_name=${CASSANDRA_SRC_DIR_NAME} --node_address=node-$i --seed_address=node-${ACTIVE_CLUSTER_SIZE}"
    echo "## Finished invoking redeploy script on node-$i"
    ) &
fi
done

wait

sleep 10

${CASSANDRA_HOME}/bin/nodetool status
