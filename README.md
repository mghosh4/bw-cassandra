# How to connect to Blue Waters node

1. SSH into Blue Waters system with `ssh <id>@bw.ncsa.illinois.edu`. Upon prompted for password, type the ordinary password followed by OTP generated password.

2. The project directory is under `/projects/sciteam/jsb`. I recommend you to create a new directory under your username, since this is shared among our research group. Scratch directory is under `/u/sciteam/<user_id>/scratch`, or you can access the same directory `~/scratch`. The scratch directory it purged after 30 days, so I ended up using the project directory.

# Initialization of Blue Waters node for the first time

2. Download Java. The default version of Java on Blue Waters is IBM's Java 1.7.0, which causes a runtime error when running Cassandra 2.1.3. We install Oracle Java 7 as recommended by Cassandra community.

    ```bash
    > wget --no-check-certificate --no-cookies --header "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/7u65-b17/jdk-7u65-linux-x64.tar.gz

 # Extract the archived file and put the java directory under the project directory.
 # For me I extracted it under '/projects/sciteam/jsb/shin1/jdk1.7.0_65'.
    ```

3. Download and configure YCSB. The original YCSB from https://github.com/brianfrankcooper/YCSB/ is outdated and not suitable for using with Cassandra. We need to download a newer version that includes `CassandraCQLClient` binding. The new version of YCSB can be found at https://github.com/jbellis/YCSB. Below is the link to the built binary of this repository.

    ```bash
    > wget http://104.236.110.182/ycsb-cassandra.tar.gz

    # Extract the archived file and put the YCSB directory under the project directory.
    # For me I extracted it under '/projects/sciteam/jsb/shin1/YCSB-cassandra-2.1.3'.
    ```
    * After extracting YCSB, you need to modify java version being used for YCSB. For some reason, YCSB does not like the IBM's Java 7 when it's running the workload. (It caused some runtime error as well.) Inside YCSB directory, open `bin/ycsb` file with a text editor. Find following line where java process is executed.
    
        ```python
        ycsb_command = ["java", "-cp", os.pathsep.join(classpath_additional + find_jars(ycsb_home, database)), \
                        COMMANDS[sys.argv[1]]["main"], "-db", db_classname] + options
        ```

    * Change `java` to the full path of the Oracle java that we just installed.

        ```python
        ycsb_command = ["/u/sciteam/shin1/scratch/jdk1.7.0_65/bin/java", "-cp", os.pathsep.join(classpath_additional + find_jars(ycsb_home, database)), \
                        COMMANDS[sys.argv[1]]["main"], "-db", db_classname] + options
        ```
        * Make sure you change the Java path to your own.


# Running in CCM(Cluster Compatibility Mode) interactively     
    The CCM lets the user to run programs on regular Linux environment.(https://bluewaters.ncsa.illinois.edu/cluster-compatibility-mode) The caveat in this mode is that the users are limited to 1024 concurrent open files, and cannot increase this limit with `ulimit` command. Therefore, submitting the job in PBS Script is necessary if one needs this limit to be higher (up to 32768).

2. Request CCM(Cluster Compatibility Mode) node with desired number of nodes, node type, and amount of time(hh:mm:ss) needed.

    ```bash
    > # qsub -I -l gres=ccm -l nodes=<# of nodes>:ppn=<# of virtual cores per node;16 or 32>:<type of node; xk or xe> -l walltime=01:00:00
    > qsub -I -l gres=ccm -l nodes=1:ppn=32:xe -l walltime=01:00:00
    ```
    * For my experiment, I used XE machines, as they provide larger memory space, and Blue Waters website claims that XE nodes are traditional compute nodes whereas XK nodes are GPU-enabled ones.(https://bluewaters.ncsa.illinois.edu/user-guide)
    * This command will take a while to be done, as it takes time to get free nodes. If you request longer time and more nodes, at peak times, it may be hard to get the desired nodes. Normally in this mode, I only request an hour or two, and usually around 16~32 compute nodes. If you need larger number of nodes for longer time, I recommend you to submit a job as a PBS script as described below.

3. Once nodes are granted, you can display availble nodes.

    ```
    > cat $HOME/.crayccm/ccm_nodelist.$PBS_JOBID | sort -u

    # nid16024   <- This is what an output should look like
    ```
4. Login to the first node.

    ```bash
    > module add ccm
    > ccmlogin
    ```

5. At this point, you should be logged into the Blue Water's CCM node. You can use regular Linux commands here and do computations

6. Or you can run script with `ccmrun` command to enable larger file number limits as following.

    ```bash
    > module add ccm
    > APRUN_XFER_LIMITS=1 ccmrun sh bw-ccmrun.sh
    ```

## Running Cassandra interactively

1. Set `JAVA_HOME` and `PATH`.

    ```bash
export JAVA_HOME=/u/sciteam/shin1/scratch/jdk1.7.0_65
export PATH=$PATH:/u/sciteam/shin1/scratch/jdk1.7.0_65
    ```

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


