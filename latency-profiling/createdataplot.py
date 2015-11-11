import os
import numpy
import math
import subprocess

coordfile = open('/projects/sciteam/jsb/ghosh1/result/coordinates')
lines = coordfile.read().splitlines()
nummachines = len(lines)
coords = numpy.zeros((nummachines,3))
count = 0
for line in lines:
	coordstr = line.split(" ")
	coords[count:] = [int(x) for x in coordstr]
	count = count + 1

print count
distarray = list()
for count1 in xrange(nummachines):
	for count2 in xrange(nummachines):
		#print("(%d,%d,%d) --- (%d,%d,%d)" % (coords[count1,0],coords[count1,1],coords[count1,2],coords[count2,0],coords[count2,1],coords[count2,2]))
		sum=abs(coords[count1,0] - coords[count2,0]) + abs(coords[count1,1] - coords[count2,1]) + abs(coords[count1,2] - coords[count2,2])
		distarray.append(sum)

hostfile = open('/projects/sciteam/jsb/ghosh1/result/hostlist')
hosts = hostfile.read().splitlines()
count = 0
for host in hosts:
	filename = '/u/sciteam/ghosh1/scratch/result/16384/nid' + host + '_latency.log'
	command = 'grep avg %s | awk \'{print $4}\' | sed \'s/\//\ /g\' | awk \'{print $2}\'' % filename
	#print command
	latencyresult = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE).communicate()[0]
	latencyvals = latencyresult.splitlines()
	for latency in latencyvals:
		print("%d %s" % (distarray[count],latency))
		count += 1
