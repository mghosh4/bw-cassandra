from unittest import TestCase
from StringIO import StringIO

import repo.ycsb_parser as ycsb_parser

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

    def test_stringio_to_string(self):
        sio = StringIO('hello world')
        s = str(sio)
        print s.__class__

    def test_parse_latency_bucket(self):
        f = open('ycsb-execution-output.txt')
        buf = f.read()
        latency_bucket = ycsb_parser.parse_latency_bucket(buf, 'read')
        print latency_bucket