import ConfigParser
from time import strftime
import pandas as pd
import os
import ycsb_parser
import re
import matplotlib.pyplot as plt


data_base_path = '../data'

def plot_throughput_vs_latency():
    emulab_data_root = '%s/raw/emulab-ramdisk' % data_base_path
    bw_data_root = '%s/raw/bw' % data_base_path

    rows = []

    data_roots = [emulab_data_root, bw_data_root]
    labels = ['emulab-ramdisk', 'bw']
    for i in range(2):
        for dir_name in os.listdir(data_roots[i]):
            if re.search('[0-9][0-9]\-[0-9][0-9]\-[0-9][0-9][0-9][0-9]$', dir_name) is not None:
                cur_dir_path = '%s/%s' % (data_roots[i], dir_name)

                result = None
                for fname in os.listdir(cur_dir_path):
                    if fname.find('output-') != -1:
                        f = open('%s/%s' % (cur_dir_path, fname))
                        cur_result = ycsb_parser.parse_execution_output(f.read())
                        if result is None:
                            result = cur_result
                        else:
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
                result.update(config_dict)

                rows.append(result)

    df = pd.DataFrame(rows)

    plt.figure()
    ax = df[df['profile'] == 'emulab-ramdisk'].plot(label='emulab-ramdisk', kind='scatter', x='overall_throughput', y='read_average_latency', color='DarkBlue')
    df[df['profile'] == 'bw'].plot(label='bw', kind='scatter', x='overall_throughput', y='read_average_latency', ax=ax, color='DarkGreen')

    # plt.show()

    output_dir_name = strftime('%m-%d-%H%M')
    os.mkdir('%s/processed/%s' % (data_base_path, output_dir_name))
    plt.savefig('%s/processed/%s/throughput-vs-latency.png' % (data_base_path, output_dir_name))
    df.to_csv('%s/processed/%s/data.csv' % (data_base_path, output_dir_name))


def main():
    plot_throughput_vs_latency()

if __name__ == "__main__":
    main()
