# How to connect to Blue Waters node

1. SSH into Blue Waters system with `ssh <id>@bw.ncsa.illinois.edu`. Upon prompted for password, type the ordinary password followed by OTP generated password.

2. Request CCM(Cluster Compatibility Mode) node for x amount of time(hh:mm:ss)
    ```bash
    > qsub -I -l gres=ccm -l nodes=1:ppn=16:xk -l walltime=01:00:00
    ```

3. Once granted nodes, you can display availble nodes.
    ```
    > cat $HOME/.crayccm/ccm_nodelist.$PBS_JOBID | sort -u
nid16024   <- This is what output should look like
    ```
4. Login to the first node.
    ```bash
    > module add ccm
    > ccmlogin
    ```

5. At this point, you should be logged into the Blue Water's CCM node. You can use regular Linux commands here and do computations

# Initialization of Blue Waters node for the first time

1. Scratch directory is under `/u/sciteam/<user_id>/scratch`. Alternatively, you can `cd ~/scratch`.

2. Download and install Java. The default version of Java on Blue Waters is IBM's Java 1.7.0, which is not new enough to run the newest version of Cassandra(2.1.3 as of today).
    ```bash
    > wget --no-check-certificate --no-cookies --header "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/7u65-b17/jdk-7u65-linux-x64.tar.gz

 # Extract the archived file and put the java directory under the scratch directory
    ```

3. Install YCSB. The original YCSB from https://github.com/brianfrankcooper/YCSB/ is outdated, and we need to download the newer version that includes `CassandraCQLClient` binding. The new version of YCSB can be found at https://github.com/jbellis/YCSB. Below is the link to the built binary of this repository.
    ```bash
> wget http://104.236.110.182/ycsb-cassandra.tar.gz
    ```

4. After extracting YCSB under scratch directory, you need to modify java version being used for YCSB. For some reason, YCSB does not like the IBM's Java 7 when it's running the workload. Inside YCSB directory, open `bin/ycsb` file with a text editor. Find following line where java process is executed.
    ```python
ycsb_command = ["java", "-cp", os.pathsep.join(classpath_additional + find_jars(ycsb_home, database)), \
                COMMANDS[sys.argv[1]]["main"], "-db", db_classname] + options
    ```

5. Change `java` to the full path of the Oracle java that we just installed.
    ```python
ycsb_command = ["/u/sciteam/shin1/scratch/jdk1.7.0_65/bin/java", "-cp", os.pathsep.join(classpath_additional + find_jars(ycsb_home, database)), \
                COMMANDS[sys.argv[1]]["main"], "-db", db_classname] + options
    ```

# Initialization needed every time logging in to Blue Waters node

1. Set `JAVA_HOME` and `PATH`.
    ```bash
export JAVA_HOME=/u/sciteam/shin1/scratch/jdk1.7.0_65
export PATH=$PATH:/u/sciteam/shin1/scratch/jdk1.7.0_65
    ```

# Running Cassandra

 1. Set up directories necessary for running Cassandra. By default, Cassandra saves its data under `/var/lib/cassandra` and log under `var/log/cassandra`. Obviously, we don't have too much access to the CCM node, and thus we should put our data under scratch directory.
    ```bash
> /u/sciteam/shin1/scratch/apache-cassandra-2.1.3/bin/cassandra
    ```
 2. To kill Cassandra, you can issue `pkill -f CassandraDaemon`.

# Run YCSB script

1. Before running YCSB workload, you have to initialize the keyspace and the column family specifically required for running YCSB.
    ```
create keyspace ycsb WITH REPLICATION = {'class' : 'SimpleStrategy', 'replication_factor': 1 };
create table ycsb.usertable (
    y_id varchar primary key,
    field0 blob,
    field1 blob,
    field2 blob,
    field3 blob,
    field4 blob,
    field5 blob,
    field6 blob,
    field7 blob,
    field8 blob,
    field9 blob);
    ```
2. You also need to add a few parameters to the default workload file as following:
    ```bash
recordcount=1000000

operationcount= 100000
workload=com.yahoo.ycsb.workloads.CoreWorkload

readallfields=true

readproportion=0.95
updateproportion=0.05
scanproportion=0
insertproportion=0

requestdistribution=zipfian

    # High number of threads is needed to accomodate high throughput.
threadcount=30

    # For CQL client
hosts=127.0.0.1
port=9042
columnfamily=usertable

histogram.buckets=10000

    # number of operations in warmup phase, if zero then don't warmup(default: 0)
warmupoperationcount=100000
    # execution time of warmup phase in milliseconds, if zero then don't warmup (default: 0)
warmupexecutiontime=30000
    ```

3. Load YCSB workload.
    ```bash
> <path_to_ycsb>/bin/ycsb load cassandra-cql -s -P <path_to_workload_file>/workload.txt > load-output.txt
    ```

4. Execute YCSB workload
    ```bash
> <path_to_ycsb>/bin/ycsb run cassandra-cql -P <path_to_workload_file>/workload-cassandra > execution-output.txt
    ```


