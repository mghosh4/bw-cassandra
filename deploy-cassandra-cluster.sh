#!/bin/bash
# DATE       AUTHOR      COMMENT
# ---------- ----------- -----------------------------------------------------
# 2015-03-20 Yosub       Initial version

for i in "$@"
do
case $i in
    --java_path=*)
    JAVA_PATH="${i#*=}"
    shift
    ;;
    --orig_cassandra_path=*)
    ORIG_CASSANDRA_PATH="${i#*=}"
    shift
    ;;
    --cassandra_home=*)
    CASSANDRA_HOME="${i#*=}"
    shift
    ;;
    --dst_host=*)
    DST_HOST="${i#*=}"
    shift
    ;;
    --seed_host=*)
    SEED_HOST="${i#*=}"
    shift
    ;;
    *)
            # unknown option
    ;;
esac
done

# Inside heredoc, \$'s delimited with \\ is not expanded locally and will be executed in remote machine
#ssh ${DST_HOST} <<EOF2
##!/bin/bash

cat <<EOF2 | ssh -t ${DST_HOST} /bin/bash

JAVA_HOME=${JAVA_PATH}
PATH=\$PATH:${JAVA_PATH}

#echo "# Killing cassandra at host ${DST_HOST}..."
#kill \$(ps aux | grep cassandra | grep -v grep | grep java | awk '{print \$2}')

#sleep 5

echo "# Cleaning up cassandra..."
rm -rf ${CASSANDRA_HOME}

echo "# Making a new Cassandra directory and copying Cassandra binary..."
mkdir ${CASSANDRA_HOME} ${CASSANDRA_HOME}/data ${CASSANDRA_HOME}/log ${CASSANDRA_HOME}/commitlog ${CASSANDRA_HOME}/saved_caches
cp -r ${ORIG_CASSANDRA_PATH} ${CASSANDRA_HOME}/cassandra

echo "# Updating cassandra.yaml config file to customize for the host ${DST_HOST}..."
bash -c "cat > ${CASSANDRA_HOME}/cassandra/conf/cassandra.yaml" <<-EOF

    cluster_name: 'Test Cluster'
    num_tokens: 256
    hinted_handoff_enabled: true
    max_hint_window_in_ms: 10800000 # 3 hours
    hinted_handoff_throttle_in_kb: 1024
    max_hints_delivery_threads: 2
    batchlog_replay_throttle_in_kb: 1024
    authenticator: AllowAllAuthenticator
    authorizer: AllowAllAuthorizer
    permissions_validity_in_ms: 2000
    partitioner: org.apache.cassandra.dht.Murmur3Partitioner
    data_file_directories:
        - ${CASSANDRA_HOME}/data
    commitlog_directory: ${CASSANDRA_HOME}/commitlog
    disk_failure_policy: stop
    commit_failure_policy: stop
    key_cache_size_in_mb:
    key_cache_save_period: 14400
    row_cache_size_in_mb: 0
    row_cache_save_period: 0
    counter_cache_size_in_mb:
    counter_cache_save_period: 7200
    saved_caches_directory: ${CASSANDRA_HOME}/saved_caches
    commitlog_sync: periodic
    commitlog_sync_period_in_ms: 10000
    commitlog_segment_size_in_mb: 32
    seed_provider:
        - class_name: org.apache.cassandra.locator.SimpleSeedProvider
          parameters:
              - seeds: "${SEED_HOST}"
    concurrent_reads: 32
    concurrent_writes: 32
    concurrent_counter_writes: 32
    memtable_allocation_type: heap_buffers
    index_summary_capacity_in_mb:
    index_summary_resize_interval_in_minutes: 60
    trickle_fsync: false
    trickle_fsync_interval_in_kb: 10240
    storage_port: 7000
    ssl_storage_port: 7001
    listen_address: ${DST_HOST}
    start_native_transport: true
    native_transport_port: 9042
    start_rpc: true
    rpc_address: ${DST_HOST}
    rpc_port: 9160
    rpc_keepalive: true
    rpc_server_type: sync
    thrift_framed_transport_size_in_mb: 15
    incremental_backups: false
    snapshot_before_compaction: false
    auto_snapshot: true
    tombstone_warn_threshold: 1000
    tombstone_failure_threshold: 100000
    column_index_size_in_kb: 64
    batch_size_warn_threshold_in_kb: 5
    compaction_throughput_mb_per_sec: 16
    sstable_preemptive_open_interval_in_mb: 50
    read_request_timeout_in_ms: 5000
    range_request_timeout_in_ms: 10000
    write_request_timeout_in_ms: 2000
    counter_write_request_timeout_in_ms: 5000
    cas_contention_timeout_in_ms: 1000
    truncate_request_timeout_in_ms: 60000
    request_timeout_in_ms: 10000
    cross_node_timeout: false
    endpoint_snitch: SimpleSnitch
    dynamic_snitch_update_interval_in_ms: 100
    dynamic_snitch_reset_interval_in_ms: 600000
    dynamic_snitch_badness_threshold: 0.1
    request_scheduler: org.apache.cassandra.scheduler.NoScheduler
    server_encryption_options:
        internode_encryption: none
        keystore: conf/.keystore
        keystore_password: cassandra
        truststore: conf/.truststore
        truststore_password: cassandra
    client_encryption_options:
        enabled: false
        keystore: conf/.keystore
        keystore_password: cassandra
    internode_compression: all
    inter_dc_tcp_nodelay: false

EOF

echo "# Updating logback.xml config file"

bash -c "cat > ${CASSANDRA_HOME}/cassandra/conf/logback.xml" <<-EOF
    <configuration scan="true">
      <jmxConfigurator />
      <appender name="FILE" class="ch.qos.logback.core.rolling.RollingFileAppender">
        <file>${CASSANDRA_HOME}/log/system.log</file>
        <rollingPolicy class="ch.qos.logback.core.rolling.FixedWindowRollingPolicy">
          <fileNamePattern>${CASSANDRA_HOME}/log/system.log.%i.zip</fileNamePattern>
          <minIndex>1</minIndex>
          <maxIndex>20</maxIndex>
        </rollingPolicy>

        <triggeringPolicy class="ch.qos.logback.core.rolling.SizeBasedTriggeringPolicy">
          <maxFileSize>20MB</maxFileSize>
        </triggeringPolicy>
        <encoder>
          <pattern>%-5level [%thread] %date{ISO8601} %F:%L - %msg%n</pattern>
          <!-- old-style log format
          <pattern>%5level [%thread] %date{ISO8601} %F (line %L) %msg%n</pattern>
          -->
        </encoder>
      </appender>

      <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
          <pattern>%-5level %date{HH:mm:ss,SSS} %msg%n</pattern>
        </encoder>
      </appender>

      <root level="INFO">
        <appender-ref ref="FILE" />
        <appender-ref ref="STDOUT" />
      </root>

      <logger name="com.thinkaurelius.thrift" level="ERROR"/>
    </configuration>
EOF

echo "# Running Cassandra"
${CASSANDRA_HOME}/cassandra/bin/cassandra

EOF2
