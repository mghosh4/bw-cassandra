class YcsbResult(object):
    def __init__(self):
        super(YcsbResult, self).__init__()
        self.update_average_latency = None
        self.read_average_latency = None
        self.overall_throughput = None
        self.update_num_operations = None
        self.read_num_operations = None
        self.overall_num_operations = None


def parse_execution_output(buf):
    all_lines = buf.split('\n')

    def is_avg_latency(x):
        return x.find('AverageLatency') is not -1

    latency_lines = filter(is_avg_latency, all_lines)

    result_dict = dict()
    for line in latency_lines:
        latency = float(line.split(' ')[2])
        if line.find('UPDATE') is not -1:
            result_dict['update_average_latency'] = latency
        elif line.find('READ') is not -1:
            result_dict['read_average_latency'] = latency

    for line in all_lines:
        if line.find('OVERALL') is not -1 and line.find('Throughput') is not -1:
            result_dict['overall_throughput'] = float(line.split(' ')[2])

    def is_num_operations(l):
        return l.find('Operations') != -1

    num_operations_lines = filter(is_num_operations, all_lines)
    for line in num_operations_lines:
        num_operations = int(float(line.split(' ')[2]))
        if line.find('UPDATE') is not -1:
            result_dict['update_num_operations'] = num_operations
        elif line.find('READ') is not -1:
            result_dict['read_num_operations'] = num_operations
        elif line.find('OVERALL') is not -1:
            result_dict['overall_num_operations'] = num_operations

    for line in all_lines:
        if line.find('RunTime') != -1:
            result_dict['runtime'] = float(line.split(' ')[2])

    return result_dict
