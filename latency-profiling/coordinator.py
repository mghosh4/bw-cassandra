import os
from threading import Thread
import sys
import profile
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s: '
                           '%(filename)s: '
                           '%(levelname)s: '
                           '%(funcName)s(): '
                           '%(lineno)d:\t'
                           '%(message)s')
logger = logging.getLogger(__name__)

src_path = '/projects/sciteam/jsb/shin1/bw-cassandra'

class RunExperimentThread(Thread):
    def __init__(self, host, packet_size, destinations):
        Thread.__init__(self)
        self.host = host
        self.packet_size = packet_size
        self.destinations = destinations

    def run(self):
        logger.debug('Running experiment at host %s' % self.host)
        result_path = '/projects/sciteam/jsb/shin1/latency/%s' % self.packet_size
        destination_hosts_str = ','.join(self.destinations)
        os.system('ssh %s sh %s/latency-profiling/testlatency.sh %s %d %s ' % (self.host, src_path, result_path, self.packet_size, destination_hosts_str))


def main():
    profile_name = sys.argv[1]
    job_id = sys.argv[2]
    pf = profile.get_profile(profile_name, job_id)

    packet_sizes = [64, 1024, 2048]
    all_hosts = pf.get_hosts()

    for packet_size in packet_sizes:
        logger.debug('Running experiment for packet_size: %d' % packet_size)
        threads = []
        # Kill cassandra on all hosts
        for host in all_hosts:
            current_thread = RunExperimentThread(host, packet_size, all_hosts)
            threads.append(current_thread)
            current_thread.start()

        for t in threads:
            t.join()


if __name__ == "__main__":
    main()
