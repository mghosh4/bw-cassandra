import os
from time import strftime, sleep
import ConfigParser
from threading import Thread
import thread
import sys
import profile
import logging
import subprocess

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s: '
                           '%(filename)s: '
                           '%(levelname)s: '
                           '%(funcName)s(): '
                           '%(lineno)d:\t'
                           '%(message)s')
logger = logging.getLogger(__name__)


class KillCassandraThread(Thread):
    def __init__(self, host):
        Thread.__init__(self)
        self.host = host

    def run(self):
        logger.debug('Killing Casandra at host %s' % self.host)
        os.system('ssh %s ps aux | grep cassandra | grep -v grep | grep java | awk \'{print $2}\' | '
                  'xargs ssh %s kill -9' % (self.host, self.host))


class CassandraDeployThread(Thread):
    def __init__(self, cassandra_path, cassandra_home, seed_host, host, java_path, mutex, output, cassandra_version):
        Thread.__init__(self)
        self.cassandra_path = cassandra_path
        self.cassandra_home = cassandra_home
        self.seed_host = seed_host
        self.host = host
        self.java_path = java_path
        self.mutex = mutex
        self.output = output
        self.cassandra_version = cassandra_version

    def run(self):
        logger.debug('Deploying cassandra at host %s' % self.host)
        ret = os.system('sh deploy-cassandra-cluster-%s.sh --orig_cassandra_path=%s --cassandra_home=%s '
                        '--seed_host=%s --dst_host=%s --java_path=%s' %
                        (self.cassandra_version, self.cassandra_path, self.cassandra_home, self.seed_host,
                         self.host, self.java_path))
        self.mutex.acquire()
        self.output.append(ret)
        self.mutex.release()
        logger.debug('Finished executing deploy cassandra thread at host %s' % self.host)


class YcsbExecuteThread(Thread):
    def __init__(self, pf, host, target_throughput, result_path, output, mutex, delay_in_millisec):
        Thread.__init__(self)
        self.pf = pf
        self.host = host
        self.target_throughput = target_throughput
        self.result_path = result_path
        self.output = output
        self.mutex = mutex
        self.delay_in_millisec = delay_in_millisec

    def run(self):
        logger.debug('Running YCSB executor thread at host %s with %d ms delay' % (self.host, self.delay_in_millisec))
        ycsb_path = self.pf.config.get('path', 'ycsb_path')
        src_path = self.pf.config.get('path', 'src_path')
        ret = os.system('ssh %s \'sh %s/ycsb-execute.sh --ycsb_path=%s --base_path=%s '
                        '--throughput=%d --host=%s --profile=%s --delay_in_millisec=%d\''
                        % (self.host, src_path, ycsb_path, self.result_path,
                           int(self.target_throughput or 0), self.host, self.pf.get_name(), self.delay_in_millisec))
        self.mutex.acquire()
        self.output.append(ret)
        self.mutex.release()
        logger.debug('Finished running YCSB executor thread at host %s' % self.host)


def run_experiment(pf, hosts, overall_target_throughput, workload_type, total_num_records, replication_factor,
                   num_cassandra_nodes, num_ycsb_nodes, total_num_ycsb_threads, cassandra_version, predict_pbs=False):
    cassandra_path = pf.config.get('path', 'cassandra_path')
    cassandra_home_base_path = pf.config.get('path', 'cassandra_home_base_path')
    ycsb_path = pf.config.get('path', 'ycsb_path')
    java_path = pf.config.get('path', 'java_path')

    result_dir_name = strftime('%m-%d-%H%M')
    result_path = '%s/%s' % (pf.get_result_base_path(), result_dir_name)
    logger.debug('Executing w/ pf=%s, num_hosts=%d, overall_target_throughput=%d, workload_type=%s, '
                 'num_records=%d, replication_factor=%d, num_cassandra_nodes=%d, result_dir_name=%s, '
                 'num_ycsb_nodes=%d, total_num_ycsb_threads=%d, cassandra_version=%s, predict_pbs=%s' %
                 (pf.get_name(), len(hosts), int(overall_target_throughput or -1), workload_type,
                  total_num_records, replication_factor, num_cassandra_nodes, result_dir_name,
                  num_ycsb_nodes, total_num_ycsb_threads, cassandra_version, predict_pbs))

    assert num_cassandra_nodes <= pf.get_max_num_cassandra_nodes()
    assert num_ycsb_nodes <= pf.get_max_num_ycsb_nodes()
    assert num_cassandra_nodes + num_ycsb_nodes <= len(hosts)

    threads = []
    # Kill cassandra on all hosts
    for host in hosts:
        current_thread = KillCassandraThread(host)
        threads.append(current_thread)
        current_thread.start()

    for t in threads:
        t.join()
    logger.debug('All Cassandra instances are killed.')
    sleep(5)

    # Cleanup, make directories, and run cassandra
    seed_host = hosts[0]
    threads = []
    output = []
    mutex = thread.allocate_lock()
    for host in hosts[0:num_cassandra_nodes]:
        cassandra_home = '%s/%s' % (cassandra_home_base_path, host)
        if host == seed_host:  # Synchronous execution for the seed host
            logger.debug('Deploying cassandra at host %s' % host)
            ret = os.system('sh deploy-cassandra-cluster-%s.sh --orig_cassandra_path=%s --cassandra_home=%s '
                            '--seed_host=%s --dst_host=%s --java_path=%s' %
                            (cassandra_version, cassandra_path, cassandra_home, seed_host, host, java_path))
            sleep(5)
        else:  # Concurrent execution for other hosts
            current_thread = CassandraDeployThread(cassandra_path, cassandra_home, seed_host, host, java_path, mutex,
                                                   output, cassandra_version)
            threads.append(current_thread)
            current_thread.start()
            sleep(5)

    for t in threads:
        t.join()

    sleep(10)

    logger.debug('Cassandra deploy threads finished with outputs: %s...' % output)
    raw_output = subprocess.Popen(['%s/bin/nodetool' % cassandra_path, '-h', seed_host, 'status'],
                                     stdout=subprocess.PIPE).communicate()[0]
    lines = raw_output.splitlines()
    filtered_lines = filter(lambda x: x.find('rack') != -1, lines)

    host_statuses = {}
    hosts_down = False
    for line in filtered_lines:
        # the real code does filtering here
        print line.rstrip()
        splitted_line = line.split()
        host = splitted_line[1]
        up = True if splitted_line[0] == 'UN' else False
        host_statuses[host] = up
        if up is False:
            hosts_down = True

    if len(host_statuses) != num_cassandra_nodes or hosts_down:
        logger.error('Cassandra is not deployed correctly!')
        raise Exception('Cassandra is not deployed correctly! %s' % str(host_statuses))

    # Running YCSB load script
    logger.debug('Running YCSB load script')
    src_path = pf.config.get('path', 'src_path')
    cassandra_nodes_hosts = ','.join(hosts[0:num_cassandra_nodes])

    num_ycsb_threads = total_num_ycsb_threads / num_ycsb_nodes
    ret = os.system('ssh %s \'sh %s/ycsb-load.sh '
                    '--cassandra_path=%s --ycsb_path=%s '
                    '--base_path=%s --num_records=%d --workload=%s '
                    '--replication_factor=%d --seed_host=%s --hosts=%s --num_threads=%d\''
                    % (hosts[num_cassandra_nodes], src_path, cassandra_path, ycsb_path,
                       result_path, total_num_records, workload_type,
                       replication_factor, seed_host, cassandra_nodes_hosts, num_ycsb_threads))
    if ret != 0:
        raise Exception('Unable to finish YCSB script')

    # Save configuration files for this experiment
    meta = ConfigParser.ConfigParser()
    meta.add_section('config')
    meta.add_section('result')
    meta.set('config', 'profile', pf.get_name())
    meta.set('config', 'num_hosts', len(hosts))
    if overall_target_throughput is not None:
        meta.set('config', 'target_throughput', overall_target_throughput)
    meta.set('config', 'workload_type', workload_type)
    meta.set('config', 'num_records', total_num_records)
    meta.set('config', 'replication_factor', replication_factor)
    meta.set('config', 'num_cassandra_nodes', num_cassandra_nodes)
    meta.set('config', 'num_ycsb_nodes', num_ycsb_nodes)
    meta.set('config', 'total_num_ycsb_threads', total_num_ycsb_threads)
    meta.set('config', 'result_dir_name', result_dir_name)
    meta.set('config', 'cassandra_version', cassandra_version)
    meta.set('config', 'predict_pbs', predict_pbs)

    base_path = pf.config.get('path', 'base_path')
    if predict_pbs:
        os.system('echo "run -b org.apache.cassandra.service:type=PBSPredictor enableConsistencyPredictionLogging" '
                  '| %s/bin/java -jar %s/jmxterm-1.0-alpha-4-uber.jar -l %s:7199' %
                  (java_path, base_path, seed_host))

    threads = []
    output = []
    mutex = thread.allocate_lock()

    # Run YCSB executor threads in parallel at each host
    logger.debug('Running YCSB execute workload at each host in parallel...')
    base_warmup_time_in_millisec = 5000
    # Delay rate : 3 seconds / 100 threads
    interval_in_millisec = num_ycsb_threads * 30
    delay_in_millisec = num_ycsb_nodes * interval_in_millisec + base_warmup_time_in_millisec

    if overall_target_throughput is not None:
        target_throughput = overall_target_throughput / num_ycsb_nodes
    else:
        target_throughput = None

    for host in hosts[num_cassandra_nodes:num_cassandra_nodes + num_ycsb_nodes]:
        current_thread = YcsbExecuteThread(pf, host, target_throughput, result_path, output, mutex, delay_in_millisec)
        threads.append(current_thread)
        current_thread.start()
        delay_in_millisec -= interval_in_millisec
        sleep(interval_in_millisec * 0.001)

    for t in threads:
        t.join()

    logger.debug('Threads finished executing with outputs: %s...' % output)

    if predict_pbs:
        pbs_probs = []
        for elapsed_time_in_ms in range(0, 50):
            # Replication factor, time, numVersions, percentileLatency

            raw_output = subprocess.Popen(['%s/bin/nodetool' % cassandra_path, '-h', seed_host,
                                          'predictconsistency %d %d 1' % (replication_factor, elapsed_time_in_ms)],
                                          stdout=subprocess.PIPE).communicate()[0]

            lines = raw_output.splitlines()
            filtered_lines = filter(lambda x: x.find('Probability of consistent reads') != -1, lines)
            line = filtered_lines[0]
            # logger.debug('elapsed_time_in_ms:%d, %s' % (elapsed_time_in_ms, line))
            logger.debug('elapsed_time_in_ms:%d' % elapsed_time_in_ms)
            logger.debug(raw_output)
            prob = float(line.split()[4])
            pbs_probs.append(prob)
        meta.set('result', 'pbs_probabilities', str(pbs_probs))

    meta_file = open('%s/meta.ini' % result_path, 'w')
    meta.write(meta_file)
    meta_file.close()


# differ throughputs
def experiment_on_throughputs(pf, num_cassandra_nodes, repeat):
    default_num_records = int(pf.config.get('experiment', 'default_num_records'))
    default_workload_type = pf.config.get('experiment', 'default_workload_type')
    default_replication_factor = int(pf.config.get('experiment', 'default_replication_factor'))

    target_throughputs = pf.get_heuristic_target_throughputs(num_cassandra_nodes)

    for run in range(repeat):
        for target_throughput in target_throughputs:
            total_num_ycsb_threads = pf.get_max_num_connections_per_cassandra_node() * num_cassandra_nodes
            total_num_records = default_num_records * num_cassandra_nodes
            num_ycsb_nodes = total_num_ycsb_threads / pf.get_max_allowed_num_ycsb_threads_per_node() + 1
            logger.debug('num_cassandra_nodes=%d, total_num_ycsb_threads=%d, num_ycsb_nodes=%d, total_num_records=%d'
                         % (num_cassandra_nodes, total_num_ycsb_threads, num_ycsb_nodes, total_num_records))

            result = run_experiment(pf,
                                    hosts=pf.get_hosts(),
                                    overall_target_throughput=target_throughput,
                                    total_num_records=default_num_records * num_cassandra_nodes,
                                    workload_type=default_workload_type,
                                    replication_factor=default_replication_factor,
                                    num_cassandra_nodes=num_cassandra_nodes,
                                    num_ycsb_nodes=num_ycsb_nodes,
                                    total_num_ycsb_threads=total_num_ycsb_threads)


def experiment_on_num_cassandra_nodes_and_throughput(pf, repeat):
    for run in range(repeat):
        for num_cassandra_nodes in range(1, pf.get_max_num_cassandra_nodes() + 1, 4):
            experiment_on_throughputs(pf, num_cassandra_nodes, 1)


def experiment_on_num_cassandra_nodes_with_no_throughput_limit(pf, repeat):
    default_num_records = int(pf.config.get('experiment', 'default_num_records'))
    default_workload_type = pf.config.get('experiment', 'default_workload_type')
    default_replication_factor = int(pf.config.get('experiment', 'default_replication_factor'))
    hosts = pf.get_hosts()
    for run in range(repeat):
        for num_cassandra_nodes in [1, 5]:
            result = run_experiment(pf,
                                    hosts=hosts,
                                    overall_target_throughput=None,
                                    total_num_records=default_num_records,
                                    workload_type=default_workload_type,
                                    replication_factor=default_replication_factor,
                                    num_cassandra_nodes=num_cassandra_nodes,
                                    num_ycsb_nodes=len(hosts) - pf.get_max_num_cassandra_nodes())


def experiment_on_num_ycsb_threads(pf):
    default_num_records = int(pf.config.get('experiment', 'default_num_records'))
    default_workload_type = pf.config.get('experiment', 'default_workload_type')
    default_replication_factor = int(pf.config.get('experiment', 'default_replication_factor'))
    hosts = pf.get_hosts()
    for num_cassandra_nodes in [1, 5, 10, 15]:
        num_threads_lower_bound = num_cassandra_nodes * 100 + 1
        num_threads_high_bound = num_cassandra_nodes * 300 + 1
        for total_num_ycsb_threads in range(num_threads_lower_bound, num_threads_high_bound, (num_threads_high_bound - num_threads_lower_bound) / 10):
            num_ycsb_nodes = total_num_ycsb_threads / pf.get_max_allowed_num_ycsb_threads_per_node() + 1
            logger.debug('num_cassandra_nodes=%d, total_num_ycsb_threads=%d, num_ycsb_nodes=%d' % (num_cassandra_nodes, total_num_ycsb_threads, num_ycsb_nodes))
            if num_ycsb_nodes > pf.get_max_num_ycsb_nodes():
                logger.debug('%d exceeds number of allowed ycsb nodes of %d...' % (num_ycsb_nodes, pf.get_max_num_ycsb_nodes()))
                continue
            result = run_experiment(pf,
                                    hosts=hosts,
                                    overall_target_throughput=None,
                                    total_num_records=default_num_records * num_cassandra_nodes,
                                    workload_type=default_workload_type,
                                    replication_factor=default_replication_factor,
                                    num_cassandra_nodes=num_cassandra_nodes,
                                    num_ycsb_nodes=num_ycsb_nodes,
                                    total_num_ycsb_threads=total_num_ycsb_threads)


def experiment_on_latency_scalability(pf):
    default_num_records = int(pf.config.get('experiment', 'default_num_records'))
    default_workload_type = pf.config.get('experiment', 'default_workload_type')
    default_replication_factor = int(pf.config.get('experiment', 'default_replication_factor'))
    hosts = pf.get_hosts()

    for i in range(3):
        for num_cassandra_nodes in [1, 5, 10, 15]:
            total_num_ycsb_threads = pf.get_max_num_connections_per_cassandra_node() * num_cassandra_nodes
            total_num_records = default_num_records * num_cassandra_nodes
            num_ycsb_nodes = total_num_ycsb_threads / pf.get_max_allowed_num_ycsb_threads_per_node() + 1
            logger.debug('num_cassandra_nodes=%d, total_num_ycsb_threads=%d, num_ycsb_nodes=%d, total_num_records=%d'
                         % (num_cassandra_nodes, total_num_ycsb_threads, num_ycsb_nodes, total_num_records))

            result = run_experiment(pf,
                                    hosts=hosts,
                                    overall_target_throughput=None,
                                    total_num_records=total_num_records,
                                    workload_type=default_workload_type,
                                    replication_factor=default_replication_factor,
                                    num_cassandra_nodes=num_cassandra_nodes,
                                    num_ycsb_nodes=num_ycsb_nodes,
                                    total_num_ycsb_threads=total_num_ycsb_threads)


def experiment_on_pbs(pf, repeat):
    default_num_records = int(pf.config.get('experiment', 'default_num_records'))
    default_workload_type = pf.config.get('experiment', 'default_workload_type')
    # num_cassandra_nodes = int(pf.config.get('experiment', 'default_num_cassandra_nodes'))
    default_replication_factor = 3
    cassandra_version = '1.2.8'
    hosts = pf.get_hosts()
    if pf.get_name() == 'bw':
        num_cassandra_nodes = 3
        num_records = default_num_records * 4
    else:
        num_cassandra_nodes = 12
        num_records = default_num_records

    overall_target_throughput = 50000

    for i in range(repeat):
        total_num_ycsb_threads = pf.get_max_num_connections_per_cassandra_node() * num_cassandra_nodes
        total_num_records = num_records * num_cassandra_nodes
        num_ycsb_nodes = total_num_ycsb_threads / pf.get_max_allowed_num_ycsb_threads_per_node() + 1
        logger.debug('Experiment on pbs')

        result = run_experiment(pf,
                                hosts=hosts,
                                overall_target_throughput=overall_target_throughput,
                                total_num_records=total_num_records,
                                workload_type=default_workload_type,
                                replication_factor=default_replication_factor,
                                num_cassandra_nodes=num_cassandra_nodes,
                                num_ycsb_nodes=num_ycsb_nodes,
                                total_num_ycsb_threads=total_num_ycsb_threads,
                                cassandra_version=cassandra_version,
                                predict_pbs=True)


def main():
    profile_name = sys.argv[1]
    job_id = sys.argv[2]
    pf = profile.get_profile(profile_name, job_id)

    # Cleanup existing result directory and create a new one
    result_file_name = strftime('%m-%d-%H%M') + '.tar.gz'

    result_base_path = pf.get_result_base_path()
    os.system('mkdir %s' % result_base_path)

    repeat = int(pf.config.get('experiment', 'repeat'))

    # Do all experiments here
    # experiment_on_throughputs(pf, int(pf.config.get('experiment', 'default_num_cassandra_nodes')), repeat)
    # experiment_on_num_cassandra_nodes_and_throughput(pf, repeat)
    # experiment_on_num_cassandra_nodes_with_no_throughput_limit(pf, repeat)
    # experiment_on_num_ycsb_threads(pf)
    # experiment_on_latency_scalability(pf)

    experiment_on_pbs(pf, repeat)

    # Copy log to result directory
    os.system('cp %s/bw-cassandra-log-%s.txt %s/bw-cassandra-log.txt' % (pf.config.get('path', 'log_path'), job_id, result_base_path))

    # Archive the result and send to remote server
    os.system('tar -czf /tmp/%s -C %s .'
              % (result_file_name, result_base_path))
    private_key_path = pf.config.get('path', 'base_path')
    os.system('scp -o StrictHostKeyChecking=no -P8888 -i %s/sshuser_key /tmp/%s sshuser@104.236.110.182:%s/'
              % (private_key_path, result_file_name, pf.get_name()))
    os.system('rm /tmp/%s' % result_file_name)


if __name__ == "__main__":
    main()
