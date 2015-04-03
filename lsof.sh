#!/bin/bash


CASSANDRA_PID=`ps aux | grep cassandra | grep -v grep | grep java | awk '{print $2}'`
echo "Number of open files: "
lsof -n -p ${CASSANDRA_PID} | wc -l

lsof -n -p ${CASSANDRA_PID}
