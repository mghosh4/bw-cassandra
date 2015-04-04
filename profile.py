import ConfigParser
import os

__author__ = 'Daniel'


class BaseProfile(object):
    def __init__(self):
        self.config = ConfigParser.SafeConfigParser()
        pass

class BlueWatersProfile(BaseProfile):
    def __init__(self):
        BaseProfile.__init__(self)
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

    def get_log_path(self):
        return '/u/sciteam/shin1/scratch'

    def get_heuristic_target_throughputs(self, num_cassandra_nodes):
        interval = 25000
        single_node_throughput = 130000
        throughput_delta_for_added_node = 50000
        safety_ratio = 1.2

        heuristic_max_throughput = int((single_node_throughput + (num_cassandra_nodes - 1) * throughput_delta_for_added_node) * safety_ratio)
        return range(interval, heuristic_max_throughput, interval)

    def get_max_num_cassandra_nodes(self):
        return 15

    def get_max_num_ycsb_nodes(self):
        return 25

    def get_max_allowed_num_ycsb_threads_per_node(self):
        return 125

    def get_max_num_connections_per_cassandra_node(self):
        return 128  # 8 connections per core (according to Solving Big Data Challenges paper)


class BlueWatersNetworkProfile(BlueWatersProfile):
    def __init__(self):
        BlueWatersProfile.__init__(self)
        self.config.read('bw-network-config.ini')

    def get_name(self):
        return 'bw-network'


class EmulabProfile(BaseProfile):
    def __init__(self):
        BaseProfile.__init__(self)
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
        interval = 15000
        single_node_throughput = 50000
        throughput_delta_for_added_node = 40000
        safety_ratio = 1.4

        heuristic_max_throughput = int((single_node_throughput + (num_cassandra_nodes - 1) * throughput_delta_for_added_node) * safety_ratio)
        return range(interval, heuristic_max_throughput, interval)

    def get_max_num_cassandra_nodes(self):
        return 15

    def get_max_num_ycsb_nodes(self):
        return 5

    def get_max_allowed_num_ycsb_threads_per_node(self):
        return 250

    def get_max_num_connections_per_cassandra_node(self):
        return 32  # 8 connections per core (according to Solving Big Data Challenges paper)


class EmulabRamdiskProfile(EmulabProfile):
    def __init__(self):
        BaseProfile.__init__(self)
        self.config.read('emulab-ramdisk-config.ini')

    def get_name(self):
        return 'emulab-ramdisk'


class EmulabNetworkProfile(EmulabProfile):
    def __init__(self):
        BaseProfile.__init__(self)
        self.config.read('emulab-network-config.ini')

    def get_name(self):
        return 'emulab-network'


def get_profile(profile_name):
    if profile_name == 'bw':
        pf = BlueWatersProfile()
    elif profile_name == 'bw-network':
        pf = BlueWatersNetworkProfile()
    elif profile_name == 'emulab':
        pf = EmulabProfile()
    elif profile_name == 'emulab-ramdisk':
        pf = EmulabRamdiskProfile()
    elif profile_name == 'emulab-network':
        pf = EmulabNetworkProfile()
    else:
        raise Exception('Specify which profile to use...')
    return pf