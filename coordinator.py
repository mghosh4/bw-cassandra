import os
from time import strftime, sleep
import ConfigParser
from threading import Thread
import thread
import sys
import profile


private_config = ConfigParser.SafeConfigParser()
private_config.read('private.ini')

workload_types = ['uniform', 'zipfian', 'latest', 'readonly']


threads = []
output = []
mutex = thread.allocate_lock()


class YcsbExecuteThread(Thread):
    def __init__(self, pf, host, throughput, result_path):
        Thread.__init__(self)
        self.pf = pf
        self.host = host
        self.throughput = throughput
        self.result_path = result_path

    def run(self):
        print 'Running YCSB executor thread at host %s' % self.host
        ycsb_path = pf.config.get('path', 'ycsb_path')
        ret = os.system('ssh %s \'%s/bin/ycsb run cassandra-cql -s -target %s -P %s/workload.txt '
                        '> %s/execution-output-%s.txt\'' % (self.host, ycsb_path, self.throughput,
                                                            self.result_path, self.result_path, self.host))
        mutex.acquire()
        output.append(ret)
        mutex.release()
        print 'Finished running YCSB executor thread at host %s' % self.host


def run_experiment(pf, hosts, throughput, workload_type, num_records, replication_factor):
    cassandra_path = pf.config.get('path', 'cassandra_path')
    cassandra_home_base_path = pf.config.get('path', 'cassandra_home_base_path')
    ycsb_path = pf.config.get('path', 'ycsb_path')
    java_path = pf.config.get('path', 'java_path')
    result_base_path = pf.config.get('path', 'result_base_path')

    # Kill cassandra on all hosts
    for host in hosts:
        print 'Killing Casandra at host %s' % host
        sudo = 'sudo' if pf.get_name() == 'emulab' else ''
        os.system('ssh %s ps aux | grep cassandra | grep -v grep | grep java | awk \'{print $2}\' | xargs %s kill' % (host, sudo))

    seed_host = hosts[0]
    # Kill, cleanup, make directories, and run cassandra
    for host in hosts:
        cassandra_home = '%s/%s' % (cassandra_home_base_path, host)
        ret = os.system('sh deploy-cassandra-cluster.sh --orig_cassandra_path=%s --cassandra_home=%s '
                        '--seed_host=%s --dst_host=%s --java_path=%s --profile=%s' %
                        (cassandra_path, cassandra_home, seed_host, host, java_path, pf.get_name()))
        sleep(30)

    # Grace period before Cassandra completely turns on before executing YCSB
    sleep(20)

    result_dir_name = strftime('%m-%d-%H%M')
    result_path = result_base_path + result_dir_name

    # Running YCSB load script
    print 'Running YCSB load script'
    ret = os.system('sh load-ycsb.sh '
                    '--cassandra_path=%s --ycsb_path=%s '
                    '--base_path=%s --throughput=%s --num_records=%d --workload=%s '
                    '--replication_factor=%d --seed_host=%s --hosts=%s'
                    % (cassandra_path, ycsb_path, result_path, throughput, num_records, workload_type,
                       replication_factor, seed_host, ','.join(hosts)))
    if ret != 0:
        raise Exception('Unable to finish YCSB script')

    # Run YCSB executor threads in parallel at each host
    print 'Running YCSB execute workload at each host in parallel...'
    for host in hosts:
        current_thread = YcsbExecuteThread(pf, host, throughput, result_path)
        threads.append(current_thread)
        current_thread.start()

    for t in threads:
        t.join()

    print 'Threads finished executing with outputs: %s...' % output


# differ throughputs
def experiment_on_throughput(pf):
    repeat = int(pf.config.get('experiment', 'repeat'))
    default_num_records = int(pf.config.get('experiment', 'default_num_records'))
    default_workload_type = pf.config.get('experiment', 'default_workload_type')
    default_replication_factor = int(pf.config.get('experiment', 'default_replication_factor'))

    throughputs = [50000, 100000, 200000, 300000]

    for run in range(repeat):
        for throughput in throughputs:
            result = run_experiment(pf,
                                    hosts=pf.get_hosts(),
                                    throughput=throughput,
                                    num_records=default_num_records,
                                    workload_type=default_workload_type,
                                    replication_factor=default_replication_factor)


def main():
    profile_name = sys.argv[1]
    if profile_name == 'bw':
        pf = profile.BlueWatersProfile()
    elif profile_name == 'emulab':
        pf = profile.EmulabProfile()
    else:
        raise Exception('Specify which profile to use...')

    # Cleanup existing result directory and create a new one
    result_file_name = strftime('%m-%d-%H%M') + '.tar.gz'
    result_base_path = pf.config.get('path', 'result_base_path')
    os.system('rm -rf %s;mkdir %s' % (result_base_path, result_base_path))

    # Do all experiments here
    experiment_on_throughput(pf)

    # Archive the result and send to remote server
    os.system('tar -czf /tmp/%s %s'
              % (result_file_name, result_base_path))
    private_key_path = pf.config.get('path', 'priate_key_path')
    os.system('scp -P8888 -i %s/sshuser_key /tmp/%s sshuser@104.236.110.182:bw/'
              % (private_key_path, result_file_name))
    os.system('rm /tmp/%s' % result_file_name)

if __name__ == "__main__":
    main()
