import ConfigParser
from time import strftime
import pandas as pd
import os
import ycsb_parser
import re
import matplotlib.pyplot as plt


data_base_path = '../data'

def plot_throughput_vs_latency():
    profile_names = ['emulab-ramdisk', 'emulab', 'emulab-network', 'bw', 'bw-network']

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
                        cur_result = ycsb_parser.parse_execution_output(f.read())
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

    df = pd.DataFrame(rows)

    output_dir_name = strftime('%m-%d-%H%M')
    os.mkdir('%s/processed/%s' % (data_base_path, output_dir_name))
    df.to_csv('%s/processed/%s/data.csv' % (data_base_path, output_dir_name))

    # Plot Emulab vs. Blue Waters on ram disk
    plt.figure()
    ax = df[df['profile'] == 'emulab-ramdisk'].plot(label='emulab-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    df[df['profile'] == 'bw'][df['num_cassandra_nodes'] == '1'].plot(label='bw-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    plt.savefig('%s/processed/%s/bw-emulab-latency-throughput.png' % (data_base_path, output_dir_name))

    # Plot BW-ramdisk vs. BW-network
    plt.figure()
    ax = df[df['profile'] == 'bw-network'].plot(label='bw-network', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    df[df['profile'] == 'bw'].plot(label='bw-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    plt.savefig('%s/processed/%s/bw-latency-throughput.png' % (data_base_path, output_dir_name))

    # Plot Emulab-ramdisk vs. Emulab-localdisk vs. Emulab-network
    plt.figure()
    ax = df[df['profile'] == 'emulab'].plot(label='emulab-localdisk', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    df[df['profile'] == 'emulab-ramdisk'].plot(label='emulab-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    df[df['profile'] == 'emulab-network'].plot(label='emulab-network', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='Red')
    plt.savefig('%s/processed/%s/emulab-latency-throughput.png' % (data_base_path, output_dir_name))

    # Plot BW-ramdisk 1 node vs. 2 node
    plt.figure()
    ax = df[df['profile'] == 'bw'][df['num_cassandra_nodes'] == '1'].plot(label='1 node', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    df[df['profile'] == 'bw'][df['num_cassandra_nodes'] == '2'].plot(label='2 nodes', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    plt.savefig('%s/processed/%s/bw-num-nodes-latency-throughput.png' % (data_base_path, output_dir_name))

    # Plot Emulab-ramdisk 1 node vs. 2 node
    plt.figure()
    ax = df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'] == '1'].plot(label='1 node', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'] == '2'].plot(label='2 nodes', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    plt.savefig('%s/processed/%s/emulab-num-nodes-latency-throughput.png' % (data_base_path, output_dir_name))

def main():
    plot_throughput_vs_latency()

if __name__ == "__main__":
    main()
