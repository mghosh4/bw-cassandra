import ConfigParser
from time import strftime
import pandas as pd
import os
import ycsb_parser
import re
import matplotlib.pyplot as plt
import matplotlib
import numpy

data_base_path = '../../data/max_throughput'


def plot_throughput_vs_latency():

    df = parse_results()
    # df = read_most_recent_csv_into_dataframe()

    output_dir_name = strftime('%m-%d-%H%M')
    try:
        os.mkdir('%s/processed/%s' % (data_base_path, output_dir_name))
        df.to_csv('%s/processed/%s/data.csv' % (data_base_path, output_dir_name))
    except:
        pass

    df['read_average_latency'] = df['read_average_latency'].apply(lambda x_: float(x_) / 1000.0)
    df['update_average_latency'] = df['update_average_latency'].apply(lambda x_: float(x_) / 1000.0)


    colors = matplotlib.cm.rainbow(numpy.linspace(0, 1, 8))
    # ['.', ',', 'o', 'v', '^', '<', '>', '1', '2', '3', '4', 's', 'p', '*', 'h', 'H', '+', 'x', 'D', 'd', '|', '_']
    markers = ['o', '^', 's', 'p', 'D', 'h', '+', 'x', '|', '_']

    plt.figure()
    plt.xlabel('number of nodes')
    plt.ylabel('latency (ms)')
    filtered_df = df[df['profile'] == 'bw']
    plt.plot(x=filtered_df['num_cassandra_nodes'], y=filtered_df['overall_throughput'], label='bw')

    filtered_df = df[df['profile'] == 'emulab-ramdisk']
    plt.plot(x=filtered_df['num_cassandra_nodes'], y=filtered_df['overall_throughput'], label='emulab')
    plt.legend(loc='best')
    plt.savefig('%s/processed/%s/num-nodes-vs-throughput.png' % (data_base_path, output_dir_name))


def parse_results():
    # profile_names = ['emulab-ramdisk', 'emulab', 'emulab-network', 'bw', 'bw-network']
    profile_names = ['bw', 'emulab-ramdisk']

    rows = []

    for profile_name in profile_names:
        data_root = '%s/raw/%s' % (data_base_path, profile_name)
        print profile_name
        for dir_name in os.listdir(data_root):
            if re.search('[0-9][0-9]\-[0-9][0-9]\-[0-9][0-9][0-9][0-9]$', dir_name) is not None:
                cur_dir_path = '%s/%s' % (data_root, dir_name)

                result = None
                print dir_name
                for fname in os.listdir(cur_dir_path):
                    if fname.find('output-') != -1:
                        f = open('%s/%s' % (cur_dir_path, fname))
                        try:
                            cur_result = ycsb_parser.parse_execution_output(f.read())
                        except Exception, e:
                            print str(e)
                            continue
                        if result is None:
                            result = cur_result
                        else:
                            print fname
                            new_result = dict()
                            new_result['update_num_operations'] = result['update_num_operations'] + cur_result['update_num_operations']
                            new_result['read_num_operations'] = result['read_num_operations'] + cur_result['read_num_operations']
                            new_result['overall_num_operations'] = result['overall_num_operations'] + cur_result['overall_num_operations']

                            new_result['update_average_latency'] = result['update_average_latency'] * result['update_num_operations'] / new_result['update_num_operations'] \
                                                                   + cur_result['update_average_latency'] * cur_result['update_num_operations'] / new_result['update_num_operations']
                            new_result['read_average_latency'] = result['update_average_latency'] * result['update_num_operations'] / new_result['update_num_operations'] \
                                                                   + cur_result['update_average_latency'] * cur_result['update_num_operations'] / new_result['update_num_operations']

                            new_result['overall_throughput'] = result['overall_throughput'] + cur_result['overall_throughput']
                            result = new_result

                meta = ConfigParser.SafeConfigParser()
                meta.read('%s/meta.ini' % cur_dir_path)
                config_dict = meta._sections['config']
                config_dict['result_dir_name'] = dir_name
                result.update(config_dict)

                rows.append(result)
    return pd.DataFrame(rows)


def read_most_recent_csv_into_dataframe():
    processed_root = '%s/processed' % data_base_path
    dir_list = os.listdir(processed_root)
    assert len(dir_list) > 0
    dir_list.sort(reverse=True)
    most_recent_dir = dir_list[0]
    return pd.read_csv('%s/%s/data.csv' % (processed_root, most_recent_dir))

def main():
    plot_throughput_vs_latency()

if __name__ == "__main__":
    main()
