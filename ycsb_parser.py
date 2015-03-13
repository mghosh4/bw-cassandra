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
            result_dict['throughput'] = float(line.split(' ')[2])

    return result_dict
