import pandas as pd
import os
import ycsb_parser
import re
import matplotlib.pyplot as plt


def plot_throughput_vs_latency():
    data_root = '../data'
    emulab_data_root = data_root + '/emulab'
    bw_data_root = data_root + '/bw'

    rows = []

    data_roots = [emulab_data_root, bw_data_root]
    labels = ['emulab', 'bw']
    for i in range(2):
        for dir_name in os.listdir(data_roots[i]):
            if re.search('[0-9][0-9]\-[0-9][0-9]\-[0-9][0-9][0-9][0-9]', dir_name) is not None:
                f = open('%s/%s/execution-output.txt' % (data_roots[i], dir_name))
                result_dict = ycsb_parser.parse_execution_output(f.read())
                result_dict['type'] = labels[i]
                rows.append(result_dict)

    df = pd.DataFrame(rows)
    plt.figure()


    ax = df[df['type'] == 'emulab'].plot(label='emulab', kind='scatter', x='throughput', y='read_average_latency', color='DarkBlue')
    df[df['type'] == 'bw'].plot(label='bw', kind='scatter', x='throughput', y='read_average_latency', ax=ax, color='DarkGreen')

    plt.show()

    print df


def main():
    plot_throughput_vs_latency()

if __name__ == "__main__":
    main()
