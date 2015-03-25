import os
from time import strftime, sleep
import ConfigParser
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


def run_experiment(neighbor_hosts, throughput, workload_type, num_records, replication_factor):
    seed_host = neighbor_hosts[0]
    # Kill, cleanup, make directories, and run cassandra
    print "my host:%s\nneighbors:%s" % (socket.gethostname(), neighbor_hosts)
    for host in neighbor_hosts:
        cassandra_home = '/tmp/cassandra-home-%s' % host
        ret = os.system('sh bw-deploy-cassandra-cluster.sh --cassandra_path=%s --cassandra_home=%s '
                        '--seed_host=%s --dst_host=%s' %
                        (cassandra_path, cassandra_home, seed_host, host))
        sleep(10)

    # Grace period before Cassandra completely turns on before executing YCSB
    sleep(20)

    output_dir_name = strftime('%m-%d-%H%M')
    output_dir_path = remote_base_path + '/data/' + output_dir_name

    # Running YCSB script
    print 'Running YCSB script'
    ret = os.system('sh bw-ycsb-script.sh '
                    '--base_path=%s --throughput=%s --num_records=%d --workload=%s '
                    '--replication_factor=%d --seed_host=%s --neighbor_hosts=%s'
                    % (output_dir_path, throughput, num_records, workload_type,
                       replication_factor, seed_host, ','.join(neighbor_hosts)))
    if ret != 0:
        raise Exception('Unable to finish YCSB script')


# differ throughputs
def experiment_on_throughput(repeat):
    for run in range(repeat):
        for throughput in throughputs:
            result = run_experiment(neighbor_hosts=get_neighbor_hosts(),
                                    throughput=throughput,
                                    num_records=default_num_records,
                                    workload_type=default_workload_type,
                                    replication_factor=default_replication_factor)


# Get host names in .crayccm file other than myself
def get_neighbor_hosts():
    hosts = set()
    my_host = socket.gethostname()
    for fn in os.listdir('/u/sciteam/shin1/.crayccm/'):
        f = open('/u/sciteam/shin1/.crayccm/%s' % fn)
        lines = f.read().splitlines()
        for line in lines:
            host = line
            # Coordinator does not participate in Cassandra cluster
            if host not in hosts:
                hosts.add(host)
        break  # Break after first file
    hosts.remove(my_host)
    return list(hosts)


def main():
    repeat = int(config.get('experiment', 'repeat'))

    experiment_on_throughput(repeat)


if __name__ == "__main__":
    main()
