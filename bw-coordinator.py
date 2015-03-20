import os
from time import strftime, sleep
import subprocess
import ConfigParser
import StringIO
import ycsb_parser

config = ConfigParser.SafeConfigParser()
config.read('bw-config.ini')

private_config = ConfigParser.SafeConfigParser()
private_config.read('private.ini')

workload_types = ['uniform', 'zipfian', 'latest', 'readonly']
throughputs = [1000, 2500, 5000, 7500, 10000, 15000]

local_result_path = config.get('path', 'local_result_path')

local_raw_result_path = local_result_path + '/raw'
local_processed_result_path = local_result_path + '/processed'

remote_base_path = config.get('path', 'remote_base_path')
cassandra_path = remote_base_path + '/apache-cassandra-2.1.3'
cassandra_home = remote_base_path + '/cassandra_home'
ycsb_home = remote_base_path + '/YCSB'

default_active_cluster_size = int(config.get('experiment', 'default_active_cluster_size'))
default_num_records = int(config.get('experiment', 'default_num_records'))
default_workload_type = config.get('experiment', 'default_workload_type')
default_replication_factor = int(config.get('experiment', 'default_replication_factor'))


def run_experiment(active_cluster_size, throughput, workload_type, num_records, replication_factor):
    print 'Turning off Cassandra...'
    os.system('pkill -f CassandraDaemon')

    # Grace period before Cassandra completely turns off
    sleep(10)

    print 'Cleaning up existing Cassandra\'s data...'
    os.system('rm -rf %s; mkdir %s %s/data %s/log %s/commitlog %s/saved_caches'
              % (cassandra_home, cassandra_home, cassandra_home, cassandra_home, cassandra_home, cassandra_home))

    output_dir_name = strftime('%m-%d-%H%M')
    output_dir_path = remote_base_path + '/data/' + output_dir_name

    # Running Cassandra cluster
    print 'Running Cassandra'
    os.system('chmod +x bw-deploy-cassandra-cluster.sh')
    ret = os.system('bw-deploy-cassandra-cluster.sh --cassandra_path=%s -cassandra_home=%s'
                    ' > /tmp/deploy-cassandra-cluster-log.txt' %
                    (cassandra_path, cassandra_home))

    # Grace period before Cassandra completely turns on before executing YCSB
    sleep(20)

    # Running YCSB script
    print 'Running YCSB script'
    os.system('chmod +x bw-ycsb-script.sh')
    ret = os.system('bw-ycsb-script.sh '
                    '--base_path=%s --throughput=%s --num_records=%d --workload=%s --replication_factor=%d'
                    % (output_dir_path, throughput, num_records, workload_type, replication_factor))
    if ret != 0:
        raise Exception('Unable to finish YCSB script')


# differ throughputs
def experiment_on_throughput(csv_file_name, repeat):
    for run in range(repeat):
        for throughput in throughputs:
            result = run_experiment(active_cluster_size=default_active_cluster_size,
                                    throughput=throughput,
                                    num_records=default_num_records,
                                    workload_type=default_workload_type,
                                    replication_factor=default_replication_factor)


def main():
    csv_file_name = '%s/%s.csv' % (local_processed_result_path, strftime('%m-%d-%H%M'))
    repeat = int(config.get('experiment', 'repeat'))

    experiment_on_throughput(csv_file_name, repeat)


if __name__ == "__main__":
    main()
