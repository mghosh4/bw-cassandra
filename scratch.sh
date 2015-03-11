
# Request CCM(Cluster Compatibility Mode) node for x amount of time
qsub -I -l gres=ccm -l nodes=1:ppn=16:xk -l walltime=01:00:00

# Display availble nodes
cat $HOME/.crayccm/ccm_nodelist.$PBS_JOBID | sort -u

# nid16024   <- This is what output should look like

# Login to the first node
module add ccm
ccmlogin


# Initialization for the first time
# Scratch directory is under '/u/sciteam/<user_id>/scratch'

	# Download and install JAVA
	wget --no-check-certificate --no-cookies --header "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/7u65-b17/jdk-7u65-linux-x64.tar.gz

	# Install YCSB
	http://104.236.110.182/ycsb-cassandra.tar.gz

	# Actually the new version of YCSB has to be used
	# https://github.com/jbellis/YCSB

	# Need to put new workload file for YCSB

	# Now error seems to be coming from IBM Java when executing YCSB
	# 22:13:30.981 0x206f7900    j9mm.107    *   ** ASSERTION FAILED ** at StandardAccessBarrier.cpp:328: ((elems == getArrayObjectDataAddress((J9VMToken*)vmThread, arrayObject)))
	# JVMDUMP039I Processing dump event "traceassert", detail "" at 2015/03/04 16:13:30 - please wait.
	# JVMDUMP032I JVM requested System dump using '/mnt/c/scratch/sciteam/shin1/core.20150304.161330.30780.0001.dmp' in response to an event
	# JVMDUMP010I System dump written to /mnt/c/scratch/sciteam/shin1/core.20150304.161330.30780.0001.dmp
	# JVMDUMP032I JVM requested Java dump using '/mnt/c/scratch/sciteam/shin1/javacore.20150304.161330.30780.0002.txt' in response to an event
	# JVMDUMP010I Java dump written to /mnt/c/scratch/sciteam/shin1/javacore.20150304.161330.30780.0002.txt
	# JVMDUMP032I JVM requested Snap dump using '/mnt/c/scratch/sciteam/shin1/Snap.20150304.161330.30780.0003.trc' in response to an event
	# JVMDUMP010I Snap dump written to /mnt/c/scratch/sciteam/shin1/Snap.20150304.161330.30780.0003.trc
	# JVMDUMP013I Processed dump event "traceassert", detail "".

	# Fixed it by adding absolute path of Oracle java in bin/ycsb file


# Start Cassandra
export JAVA_HOME=/u/sciteam/shin1/scratch/jdk1.7.0_65
export PATH=$PATH:/u/sciteam/shin1/scratch/jdk1.7.0_65
/u/sciteam/shin1/scratch/apache-cassandra-2.1.3/bin/cassandra

# Run YCSB script
sh /u/sciteam/shin1/scratch/bw-ycsb-script.sh --base_path=/u/sciteam/shin1/scratch/data --throughput=1000 --num_records=1000000 --workload=zipfian --replication_factor=1

# # Create keyspace and column family for YCSB

# # Load YCSB workload
# YCSB/bin/ycsb load cassandra-cql -P YCSB/workloads/workload-cassandra > output-load.txt

# # Execute YCSB workload
# YCSB/bin/ycsb run cassandra-cql -P YCSB/workloads/workload-cassandra > output-run.txt



