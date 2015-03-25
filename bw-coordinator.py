import os
from time import strftime, sleep
import subprocess
import ConfigParser
import StringIO
import ycsb_parser
import socket

config = ConfigParser.SafeConfigParser()
config.read('bw-config.ini')

private_config = ConfigParser.SafeConfigParser()
private_config.read('private.ini')

workload_types = ['uniform', 'zipfian', 'latest', 'readonly']
throughputs = [10000, 20000, 30000, 40000, 50000]

local_result_path = config.get('path', 'local_result_path')

local_raw_result_path = local_result_path + '/raw'
local_processed_result_path = local_result_path + '/processed'

remote_base_path = config.get('path', 'remote_base_path')
cassandra_path = remote_base_path + '/apache-cassandra-2.1.3'
ycsb_home = remote_base_path + '/YCSB'

default_active_cluster_size = int(config.get('experiment', 'default_active_cluster_size'))
default_num_records = int(config.get('experiment', 'default_num_records'))
default_workload_type = config.get('experiment', 'default_workload_type')
default_replication_factor = int(config.get('experiment', 'default_replication_factor'))


def run_experiment(hosts, throughput, workload_type, num_records, replication_factor):
    seed_host = hosts[0]
    my_host = socket.gethostname()
    # Kill, cleanup, make directories, and run cassandra
    for host in hosts:
        # Coordinator does not participate in Cassandra cluster
        if host is not my_host:
            cassandra_home = '/tmp/cassandra-home-%s' % host
            ret = os.system('sh bw-deploy-cassandra-cluster.sh --cassandra_path=%s --cassandra_home=%s '
                            '--seed_host=%s --dst_host=%s' %
                            (cassandra_path, cassandra_home, seed_host, host))

    # Grace period before Cassandra completely turns on before executing YCSB
    sleep(20)

    output_dir_name = strftime('%m-%d-%H%M')
    output_dir_path = remote_base_path + '/data/' + output_dir_name

    # Running YCSB script
    print 'Running YCSB script'
    ret = os.system('sh bw-ycsb-script.sh '
                    '--base_path=%s --throughput=%s --num_records=%d --workload=%s --replication_factor=%d'
                    % (output_dir_path, throughput, num_records, workload_type, replication_factor))
    if ret != 0:
        raise Exception('Unable to finish YCSB script')


# differ throughputs
def experiment_on_throughput(repeat):
    for run in range(repeat):
        for throughput in throughputs:
            result = run_experiment(hosts=get_hosts(),
                                    throughput=throughput,
                                    num_records=default_num_records,
                                    workload_type=default_workload_type,
                                    replication_factor=default_replication_factor)


def get_hosts():
    hosts = set()
    for fn in os.listdir('/u/sciteam/shin1/.crayccm/'):
        f = open('/u/sciteam/shin1/.crayccm/%s' % fn)
        lines = f.read().splitlines()
        for line in lines:
            host = line
            if host not in hosts:
                hosts.add(host)
        break  # Break after first file
    return hosts


def main():
    repeat = int(config.get('experiment', 'repeat'))

    experiment_on_throughput(repeat)


if __name__ == "__main__":
    main()
