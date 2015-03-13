import os
from time import strftime, sleep
import subprocess
import ConfigParser
import StringIO
import pandas as pd
import ycsb_parser
from twilio.rest import TwilioRestClient

config = ConfigParser.SafeConfigParser()
config.read('emulab-config.ini')

private_config = ConfigParser.SafeConfigParser()
private_config.read('private.ini')
tc = TwilioRestClient(private_config.get('twilio', 'account_sid'), private_config.get('twilio', 'auth_token'))

workload_types = ['uniform', 'zipfian', 'latest', 'readonly']
throughputs = [1000, 2500, 5000, 7500, 10000, 15000]

local_base_path = config.get('path', 'local_base_path')
local_result_path = config.get('path', 'local_result_path')
local_raw_result_path = local_result_path + '/raw'
local_processed_result_path = local_result_path + '/processed'

remote_base_path = config.get('path', 'remote_base_path')

default_active_cluster_size = int(config.get('experiment', 'default_active_cluster_size'))
default_cluster_size = int(config.get('experiment', 'default_cluster_size'))
default_num_records = int(config.get('experiment', 'default_num_records'))
default_workload_type = config.get('experiment', 'default_workload_type')
default_replication_factor = int(config.get('experiment', 'default_replication_factor'))


def run_experiment(cluster_size, active_cluster_size, throughput, workload_type, num_records, replication_factor):
    # Executing hard reset of Cassandra cluster on Emulab
    print 'Executing hard reset of Cassandra cluster on Emulab'
    ret = os.system('./remote-deploy-cassandra-cluster.sh'
                    ' --local_base_path=%s --cluster_size=%d --active_cluster_size=%d --throughput=%d'
                    % (local_base_path, cluster_size, active_cluster_size, throughput))
    if ret != 0:
        raise Exception('Unable to finish remote-deploy-cassandra-cluster.sh')

    # Grace period for Cassandra to startup before starting YCSB workload
    sleep(10)

    output_dir_name = strftime('%m-%d-%H%M')
    output_dir_path = '/tmp/' + output_dir_name
    # SSH into server and run YCSB script
    print 'SSH into server and run YCSB script'
    ret = os.system('ssh yossupp@node-0.bw-cassandra.ISS.emulab.net '
                    '\'sudo %s/emulab-ycsb-script.sh '
                    '--base_path=%s --throughput=%s --num_records=%d --workload=%s --replication_factor=%d\''
                    % (remote_base_path, output_dir_path, throughput, num_records, workload_type, replication_factor))
    if ret != 0:
        raise Exception('Unable to finish YCSB script')

    try:
        out = subprocess.check_output(('ssh yossupp@node-0.bw-cassandra.ISS.emulab.net \'cat %s/execution-output.txt\''
                                       % output_dir_path), shell=True)
        buf = StringIO.StringIO(out)
        result = ycsb_parser.parse_execution_output(buf)

    finally:
        os.system('ssh yossupp@node-0.bw-cassandra.ISS.emulab.net \'tar -czf %s.tar.gz -C %s %s \''
                  % (output_dir_path, '/tmp', output_dir_name))
        os.system('scp yossupp@node-0.bw-cassandra.ISS.emulab.net:%s.tar.gz %s/'
                  % (output_dir_path, local_raw_result_path))
        os.system('tar -xzf %s/%s.tar.gz -C %s/' % (local_raw_result_path, output_dir_name, local_raw_result_path))
        os.system('rm -f %s/%s.tar.gz' % (local_raw_result_path, output_dir_name))

    result['base_directory_name'] = output_dir_name
    result['workload_type'] = workload_type
    result['num_records'] = num_records
    result['throughput'] = throughput
    result['num_nodes'] = active_cluster_size
    result['replication_factor'] = replication_factor
    return result


# differ throughputs
def experiment_on_throughput(csv_file_name, repeat):
    for run in range(repeat):
        for throughput in throughputs:
            result = run_experiment(cluster_size=default_cluster_size,
                                    active_cluster_size=default_active_cluster_size,
                                    throughput=throughput,
                                    num_records=default_num_records,
                                    workload_type=default_workload_type,
                                    replication_factor=default_replication_factor)
            append_row_to_csv(csv_file_name, result)


def append_row_to_csv(csv_file_name, row):
    df = pd.DataFrame([row])
    if os.path.isfile(csv_file_name):
        with open(csv_file_name, 'a') as f:
            df.to_csv(f, header=False)
    else:
        df.to_csv(csv_file_name)


def main():
    csv_file_name = '%s/%s.csv' % (local_processed_result_path, strftime('%m-%d-%H%M'))
    repeat = int(config.get('experiment', 'repeat'))

    experiment_on_throughput(csv_file_name, repeat)

    # try:
    #     csv_file_name = '%s/%s.csv' % (local_processed_result_path, strftime('%m-%d-%H%M'))
    #     repeat = int(config.get('experiment', 'repeat'))
    #
    #     experiment_on_throughput(csv_file_name, repeat)
    #
    # except Exception, e:
    #     tc.messages.create(from_=private_config.get('personal', 'twilio_number'),
    #                        to=private_config.get('personal', 'phone_number'),
    #                        body='Exp. failed w/:\n%s' % str(e))
    #     raise
    # tc.messages.create(from_=private_config.get('personal', 'twilio_number'),
    #                    to=private_config.get('personal', 'phone_number'),
    #                    body='Experiment done!')

if __name__ == "__main__":
    main()
