import ConfigParser
from time import strftime
import os
import re

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import numpy
import time

from analysis import ycsb_parser

data_base_path = os.path.abspath('../../data/consistency')

output_dir_name = time.strftime('%m-%d-%H%M')
output_dir_path = '%s/processed/%s' % (data_base_path, output_dir_name)
try:
    os.mkdir(output_dir_path)
except:
    pass

raw_data_root = '%s/raw' % data_base_path

profile_dicts = {}
for profile_name in ['bw', 'emulab']:
    for dir_name in os.listdir('%s/%s' % (raw_data_root, profile_name)):
        if re.search('[0-9][0-9]\-[0-9][0-9]\-[0-9][0-9][0-9][0-9]$', dir_name) is not None:
            cur_dir_path = '%s/%s/%s' % (raw_data_root, profile_name, dir_name)

            print 'CDF', profile_name, dir_name

            meta = ConfigParser.SafeConfigParser()
            meta.read('%s/meta.ini' % cur_dir_path)
            config_dict = meta._sections['config']
            config_dict['result_dir_name'] = dir_name

            output_fs = filter(lambda x: x.find('execution-output-') != -1 and x.find('stderr') == -1, os.listdir(cur_dir_path))
            aggregate_dicts = {'read': None, 'update': None}
            for fname in output_fs:
                f = open('%s/%s' % (cur_dir_path, fname))
                f_buf = f.read()
                for rw in ['read', 'update']:
                    bucket_dict = ycsb_parser.parse_latency_bucket(f_buf, rw)
                    if aggregate_dicts[rw] is None:
                        aggregate_dicts[rw] = bucket_dict
                    else:
                        for key, value in bucket_dict.iteritems():
                            if key in aggregate_dicts[rw]:
                                aggregate_dicts[rw][key] += value
                            else:
                                aggregate_dicts[rw][key] = value

            # profile_dicts[profile_name] = aggregate_dicts
            if profile_name not in profile_dicts:
                profile_dicts[profile_name] = aggregate_dicts
            else:
                for rw in aggregate_dicts.keys():
                    for key, value in aggregate_dicts[rw].iteritems():
                        if key in profile_dicts[profile_name][rw]:
                            profile_dicts[profile_name][rw][key] += value
                        else:
                            profile_dicts[profile_name][rw][key] = value
                            

for profile_name in profile_dicts.keys():
    aggregate_dicts = profile_dicts[profile_name]
    for rw in aggregate_dicts.keys():
        aggregate_dict = aggregate_dicts[rw]
        total_num_operations = reduce(lambda x, y: x + y, aggregate_dict.values())
        for key in aggregate_dict.keys():
            aggregate_dict[key] = float(aggregate_dict[key]) / total_num_operations
        rows = []
        for i, key in enumerate(sorted(aggregate_dict.keys())):
            if i == 0:
                rows.append({'0latency': key + 1, '1cumulative': aggregate_dict[key]})
            else:
                cum = rows[i - 1]['1cumulative'] + aggregate_dict[key]
                rows.append({'0latency': key + 1, '1cumulative': cum})
        df = pd.DataFrame(rows)
        df.to_csv('%s/cumulative-%s-%s.csv' % (output_dir_path, rw, profile_name), header=False, index=False)


for rw in ['read', 'update']:
    paths = filter(lambda x: re.search('.*cumulative\-%s\-.*\.csv' % rw, x) is not None,
                   ['%s/%s' % (output_dir_path, x) for x in os.listdir(output_dir_path)])
    bw_path = filter(lambda x: x.find('bw') != -1, paths)[0]
    emulab_path = filter(lambda x: x.find('emulab') != -1, paths)[0]

    output_path = '%s/%s-cdf.png' % (output_dir_path, rw)

    os.system('./plot-latency-cdf.sh --rw=%s --output_path=%s --bw=%s --emulab=%s' %
              (rw, output_path, bw_path, emulab_path))