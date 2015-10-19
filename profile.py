import ConfigParser
import os
import urllib2
import subprocess

__author__ = 'Daniel'


class BaseProfile(object):
    def __init__(self, job_id):
        self.config = ConfigParser.SafeConfigParser()
        self.job_id = job_id

    def get_result_base_path(self):
        result_base_path = '%s/%s' % (self.config.get('path', 'result_base_path'), self.job_id)
        return result_base_path


class BlueWatersProfile(BaseProfile):
    def __init__(self, job_id):
        BaseProfile.__init__(self, job_id)
        self.config.read('bw-config.ini')

    # Get host names in .crayccm file
    def get_hosts(self):
        hosts = set()
        for fn in os.listdir('/u/sciteam/shin1/.crayccm/'):
            f = open('/u/sciteam/shin1/.crayccm/%s' % fn)
            lines = f.read().splitlines()
            for line in lines:
                host = line
                hosts.add(host)

            break  # Break after first file
        return list(hosts)

    def get_name(self):
        return 'bw'

    def get_heuristic_target_throughputs(self, num_cassandra_nodes):
        single_node_throughput = 100000
        throughput_delta_for_added_node = 100000
        safety_ratio = 2.0

        heuristic_max_throughput = int((single_node_throughput + (num_cassandra_nodes - 1) * throughput_delta_for_added_node) * safety_ratio)
        measurement_interval = heuristic_max_throughput / 10
        return range(measurement_interval, heuristic_max_throughput, measurement_interval)

    def get_max_num_cassandra_nodes(self):
        return 15

    def get_max_num_ycsb_nodes(self):
        return 25

    def get_max_allowed_num_ycsb_threads_per_node(self):
        return 128

    def get_max_num_connections_per_cassandra_node(self):
        return 128  # 8 connections per core (according to Solving Big Data Challenges paper)


class GCloudProfile(BaseProfile):
    def __init__(self, job_id):
        BaseProfile.__init__(self, job_id)
        self.config.read('gcloud-config.ini')

    @staticmethod
    def get_instance_hostname():
        req = urllib2.Request(
            'http://metadata/computeMetadata/v1/instance/hostname')
        req.add_header('Metadata-Flavor', 'Google')
        res = urllib2.urlopen(req)
        return res.read().split('.')[0]

    @staticmethod
    def get_instance_group_name():
        # instance-group-X
        return 'instance-group-%d' % int(GCloudProfile.get_instance_hostname()[len('instance-group-')])

    def get_hosts(self):
        lines = subprocess.check_output(['sudo', 'gcloud', 'compute', 'instance-groups', 'list-instances', GCloudProfile.get_instance_group_name(), '--zone', 'us-central1-f'])
        lines = lines.split('\n')
        lines = lines[1:]
        return sorted(filter(lambda l: len(l) > 0, map(lambda l: l.split(' ')[0], lines)))

    def get_name(self):
        return 'gcloud'

    def get_log_path(self):
        return '/tmp'

    def get_heuristic_target_throughputs(self, num_cassandra_nodes):
        single_node_throughput = 100000
        throughput_delta_for_added_node = 100000
        safety_ratio = 2.0

        heuristic_max_throughput = int((single_node_throughput + (num_cassandra_nodes - 1) * throughput_delta_for_added_node) * safety_ratio)
        measurement_interval = heuristic_max_throughput / 10
        return range(measurement_interval, heuristic_max_throughput, measurement_interval)

    def get_max_num_cassandra_nodes(self):
        return 15

    def get_max_num_ycsb_nodes(self):
        return 25

    def get_max_allowed_num_ycsb_threads_per_node(self):
        return 256

    def get_max_num_connections_per_cassandra_node(self):
        return 128  # 8 connections per core (according to Solving Big Data Challenges paper)


class EmulabProfile(BaseProfile):
    def __init__(self, job_id):
        BaseProfile.__init__(self, job_id)
        self.config.read('emulab-config.ini')

    def get_hosts(self):
        hosts = set()
        f = open('/etc/hosts')
        lines = f.read().splitlines()
        for line in lines:
            tokens = line.split()
            if len(tokens) < 4:
                continue
            elif tokens[3].find('node') == -1:
                continue
            else:
                host = tokens[3]
                hosts.add(host)
        return list(hosts)

    def get_name(self):
        return 'emulab'

    def get_log_path(self):
        return '/tmp'

    def get_heuristic_target_throughputs(self, num_cassandra_nodes):
        single_node_throughput = 15000
        throughput_delta_for_added_node = 15000
        safety_ratio = 2.0

        heuristic_max_throughput = int((single_node_throughput + (num_cassandra_nodes - 1) * throughput_delta_for_added_node) * safety_ratio)
        measurement_interval = heuristic_max_throughput / 10
        return range(measurement_interval, heuristic_max_throughput, measurement_interval)

    def get_max_num_cassandra_nodes(self):
        return 15

    def get_max_num_ycsb_nodes(self):
        return 2

    def get_max_allowed_num_ycsb_threads_per_node(self):
        return 256

    def get_max_num_connections_per_cassandra_node(self):
        return 32  # 8 connections per core (according to Solving Big Data Challenges paper)


def get_profile(profile_name, job_id):
    if profile_name == 'bw':
        pf = BlueWatersProfile(job_id)
    elif profile_name == 'gcloud':
        pf = GCloudProfile(job_id)
    elif profile_name == 'emulab':
        pf = EmulabProfile(job_id)
    else:
        raise Exception('Specify which profile to use...')
    return pf