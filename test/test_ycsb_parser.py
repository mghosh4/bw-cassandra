from unittest import TestCase

import ycsb_parser

__author__ = 'Daniel'


class TestYcsbParser(TestCase):
    def test_pandas_dict_append(self):
        f = open('ycsb-execution-output.txt')
        buf = f.read()
        result_dict = ycsb_parser.parse_execution_output(buf)

        assert len(result_dict) == 3
        assert result_dict['read_average_latency'] is not None
        assert result_dict['throughput'] is not None
        assert result_dict['update_average_latency'] is not None

        print result_dict