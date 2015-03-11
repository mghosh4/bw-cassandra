#!/bin/bash
# DATE       AUTHOR      COMMENT
# ---------- ----------- -----------------------------------------------------
# 2014-08-19 Yosub       Initial version
# 2015-03-10 Yosub       Updated for BW-Cassandra project

for i in "$@"
do
case $i in
    --local_base_path=*)
    LOCAL_BASE_PATH="${i#*=}"
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
    *)
            # unknown option
    ;;
esac
done


CASSANDRA_SRC_DIR_BASE=${LOCAL_BASE_PATH}
CASSANDRA_SRC_DIR_NAME=apache-cassandra-2.1.3
#CASSANDRA_SRC_DIR=${CASSANDRA_SRC_DIR_BASE}/${CASSANDRA_SRC_DIR_NAME}
CASSANDRA_SRC_TAR_FILE=apache-cassandra-2.1.3.tar.gz
SSH_USER=yossupp
SSH_URL=node-0.bw-cassandra.ISS.emulab.net
REMOTE_BASE_DIR=/proj/ISS/shin14/bw-cassandra
REMOTE_SCRIPT_DIR=${REMOTE_BASE_DIR}
REMOTE_REDEPLOY_SCRIPT=${REMOTE_SCRIPT_DIR}/redeploy-node-script.sh
REMOTE_DEPLOY_CLUSTER_SCRIPT=${REMOTE_SCRIPT_DIR}/deploy-cassandra-cluster.sh
CASSANDRA_HOME=/opt/cassandra

echo "## Remote deploying Cassandra cluster with cluster_size=${CLUSTER_SIZE}, active_cluster_size=${ACTIVE_CLUSTER_SIZE}"

echo "## Copying remote scripts to remote host"
scp deploy-cassandra-cluster.sh $SSH_USER@$SSH_URL:$REMOTE_SCRIPT_DIR/
scp redeploy-node-script.sh $SSH_USER@$SSH_URL:$REMOTE_SCRIPT_DIR/
scp init-node-script-ubuntu12.04.sh $SSH_USER@$SSH_URL:$REMOTE_SCRIPT_DIR/
scp emulab-ycsb-script.sh $SSH_USER@$SSH_URL:$REMOTE_SCRIPT_DIR/

#echo "## Archiving Cassandra source files..."
#cd $CASSANDRA_SRC_DIR_BASE
#tar -czf $CASSANDRA_SRC_TAR_FILE -C $CASSANDRA_SRC_DIR_BASE $CASSANDRA_SRC_DIR_NAME

echo "## Uploading archived Cassandra source to remote host"
scp ${CASSANDRA_SRC_DIR_BASE}/${CASSANDRA_SRC_TAR_FILE} ${SSH_USER}@${SSH_URL}:${REMOTE_BASE_DIR}

# Clean up tar file
#rm $CASSANDRA_SRC_DIR_BASE/$CASSANDRA_SRC_TAR_FILE

echo "## Executing cluster redeploy script on remote host"
ssh -T $SSH_USER@$SSH_URL "/bin/bash ${REMOTE_DEPLOY_CLUSTER_SCRIPT} --basedir=${REMOTE_BASE_DIR} --cluster_size=${CLUSTER_SIZE} --active_cluster_size=${ACTIVE_CLUSTER_SIZE} --src_dir_name=${CASSANDRA_SRC_DIR_NAME}"
