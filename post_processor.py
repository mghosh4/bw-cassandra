import ConfigParser
from time import strftime
import pandas as pd
import os
import ycsb_parser
import re
import matplotlib.pyplot as plt
import matplotlib
import numpy

data_base_path = '../data'

def plot_throughput_vs_latency():

    df = parse_results()
    # df = read_most_recent_csv_into_dataframe()

    df_1node = df[df['num_cassandra_nodes'] == 1]

    output_dir_name = strftime('%m-%d-%H%M')
    try:
        os.mkdir('%s/processed/%s' % (data_base_path, output_dir_name))
        df.to_csv('%s/processed/%s/data.csv' % (data_base_path, output_dir_name))
    except:
        pass

    # # Plot Emulab vs. Blue Waters on ram disk
    # plt.figure()
    # ax = df_1node[df_1node['profile'] == 'emulab-ramdisk'].plot(label='emulab-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    # df_1node[df_1node['profile'] == 'bw'].plot(label='bw-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    # plt.savefig('%s/processed/%s/bw-emulab-latency-throughput.png' % (data_base_path, output_dir_name))
    #
    # # Plot BW-ramdisk vs. BW-network
    # plt.figure()
    # ax = df_1node[df_1node['profile'] == 'bw-network'].plot(label='bw-network', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    # df_1node[df_1node['profile'] == 'bw'].plot(label='bw-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    # plt.savefig('%s/processed/%s/bw-latency-throughput.png' % (data_base_path, output_dir_name))
    #
    # # Plot Emulab-ramdisk vs. Emulab-localdisk vs. Emulab-network
    # plt.figure()
    # ax = df_1node[df_1node['profile'] == 'emulab'].plot(label='emulab-localdisk', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    # df_1node[df_1node['profile'] == 'emulab-ramdisk'].plot(label='emulab-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')
    # df_1node[df_1node['profile'] == 'emulab-network'].plot(label='emulab-network', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='Red')
    # plt.savefig('%s/processed/%s/emulab-latency-throughput.png' % (data_base_path, output_dir_name))


    colors = matplotlib.cm.rainbow(numpy.linspace(0, 1, 8))
    # ['.', ',', 'o', 'v', '^', '<', '>', '1', '2', '3', '4', 's', 'p', '*', 'h', 'H', '+', 'x', 'D', 'd', '|', '_']
    markers = ['o', '^', 's', 'p', '*', 'h', '+', 'x', 'D', '|', '_']

    noise_filter_ratio = 0.15
    throughput_range = 300000
    latency_range = 30000
    # Plot BW-ramdisk for varying number of nodes
    plt.figure()
    plt.xlim(0, throughput_range)
    plt.ylim(0, latency_range)
    for i in range(0, 5, 1):
        cur_df = df[df['profile'] == 'bw'][df['num_cassandra_nodes'].astype('int') == (i + 1)][df['target_throughput'].astype('float') - df['overall_throughput'].astype('float') < df['target_throughput'].astype('float') * noise_filter_ratio]
        plt.scatter(x=cur_df['overall_throughput'], y=cur_df['read_average_latency'], c=colors[i], marker=markers[i],
                    label='bw %d nodes' % (i + 1))
    plt.legend(loc='best')
    plt.savefig('%s/processed/%s/bw-num-nodes-latency-throughput.png' % (data_base_path, output_dir_name))

    for i in range(0, 5):
        plt.figure()
        plt.xlim(0, throughput_range)
        plt.ylim(0, latency_range)
        cur_df = df[df['profile'] == 'bw'][df['num_cassandra_nodes'].astype('int') == (i + 1)][df['target_throughput'].astype('float') - df['overall_throughput'].astype('float') < df['target_throughput'].astype('float') * noise_filter_ratio]
        plt.scatter(x=cur_df['overall_throughput'], y=cur_df['read_average_latency'], c=colors[i], marker=markers[i],
                    label='bw %d nodes' % (i + 1))
        for label, x, y in zip(cur_df['target_throughput'], cur_df['overall_throughput'], cur_df['read_average_latency']):
            plt.annotate(label, xy=(x, y), xytext=(-10, 5), textcoords='offset points', size='xx-small')
        plt.legend(loc='best')
        plt.savefig('%s/processed/%s/bw-%d-nodes-latency-throughput.png' % (data_base_path, output_dir_name, (i + 1)))

    # Plot Emulab-ramdisk for varying number of nodes
    plt.figure()
    plt.xlim(0, throughput_range)
    plt.ylim(0, latency_range)
    for i in range(0, 7, 1):
        cur_df = df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'].astype('int') == (i + 1)][df['target_throughput'].astype('float') - df['overall_throughput'].astype('float') < df['target_throughput'].astype('float') * noise_filter_ratio]
        plt.scatter(x=cur_df['overall_throughput'], y=cur_df['read_average_latency'], c=colors[i], marker=markers[i],
                    label='emulab %d nodes' % (i + 1))
    plt.legend(loc='best')
    plt.savefig('%s/processed/%s/emulab-num-nodes-latency-throughput.png' % (data_base_path, output_dir_name))

    for i in range(0, 8):
        plt.figure()
        plt.xlim(0, throughput_range)
        plt.ylim(0, latency_range)
        cur_df = df[df['profile'] == 'emulab-ramdisk'][df['num_cassandra_nodes'].astype('int') == (i + 1)][df['target_throughput'].astype('float') - df['overall_throughput'].astype('float') < df['target_throughput'].astype('float') * noise_filter_ratio]
        plt.scatter(x=cur_df['overall_throughput'], y=cur_df['read_average_latency'], c=colors[i], marker=markers[i],
                    label='emulab %d nodes' % (i + 1))
        for label, x, y in zip(cur_df['target_throughput'], cur_df['overall_throughput'], cur_df['read_average_latency']):
            plt.annotate(label, xy=(x, y), xytext=(-10, 5), textcoords='offset points', size='xx-small')
        plt.legend(loc='best')
        plt.savefig('%s/processed/%s/emulab-%d-nodes-latency-throughput.png' % (data_base_path, output_dir_name, (i + 1)))


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
