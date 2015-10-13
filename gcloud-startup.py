#! /usr/bin/python

# Startup script for Cassandra

import urllib2
from subprocess import STDOUT, check_call
import os
import subprocess
from pwd import getpwnam
import time


def get_external_ip():
    req = urllib2.Request(
        'http://metadata/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip')
    req.add_header('Metadata-Flavor', 'Google')
    res = urllib2.urlopen(req)
    return res.read()


def get_instance_hostname():
    req = urllib2.Request(
        'http://metadata/computeMetadata/v1/instance/hostname')
    req.add_header('Metadata-Flavor', 'Google')
    res = urllib2.urlopen(req)
    return res.read().split('.')[0]


def get_instance_group_name():
    # instance-group-X
    return 'instance-group-%d' % int(get_instance_hostname()[len('instance-group-')])


def get_hosts():
    lines = subprocess.check_output(['sudo', 'gcloud', 'compute', 'instance-groups', 'list-instances', get_instance_group_name(), '--zone', 'us-central1-f'])
    lines = lines.split('\n')
    lines = lines[1:]
    return sorted(filter(lambda l: len(l) > 0, map(lambda l: l.split(' ')[0], lines)))


print('Setting the limit of the number of open files to be higher')
with open('/etc/security/limits.conf', 'a') as limits_conf:
    limits_conf.write('''
*    -   memlock  unlimited
*    -   nofile   500000
root    -   memlock  unlimited
root    -   nofile   500000
''')

username = 'yosub_shin_0'
home_directory_path = '/home/%s' % username
uid = getpwnam(username)[2]

print('Downloading private key for scp...')
check_call(['/usr/local/bin/gsutil', 'cp', 'gs://bw-cassandra/sshuser_gcloud', '%s/' % home_directory_path],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)
os.chown('%s/sshuser_gcloud' % home_directory_path, uid, uid)

os.setgid(uid)
os.setuid(uid)

# Let's install binaries first before we get hosts list (May potentially not get every host)
print('Installing binaries...')
check_call(['sudo', 'apt-get', 'install', '-y', 'git', 'emacs', 'byobu', 'apt-transport-https'],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)

instance_group_hosts = get_hosts()
print('instance group hosts: %s' % ', '.join(instance_group_hosts))
master_hostname = instance_group_hosts[0]
print('master hostname: %s' % master_hostname)
instance_hostname = get_instance_hostname()
print('Current instance hostname: %s' % instance_hostname)
if instance_hostname == master_hostname:
    print('Current host is the master node')

name_node_hostname = master_hostname
os.chdir(home_directory_path)

# Download Java
print('Downloading Java...')
check_call(['wget', '--no-check-certificate', '--no-cookies', '--header', 'Cookie: oraclelicense=accept-securebackup-cookie', 'http://download.oracle.com/otn-pub/java/jdk/7u65-b17/jdk-7u65-linux-x64.tar.gz'],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)
check_call(['tar', '-xzf', 'jdk-7u65-linux-x64.tar.gz'],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)

with open('.bashrc', 'a') as bashrc:
    bashrc.write('export JAVA_HOME=%s/jdk1.7.0_65/jre\nexport PATH=$PATH:$JAVA_HOME/bin' % home_directory_path)
os.environ['JAVA_HOME'] = '%s/jdk1.7.0_65/jre' % home_directory_path
check_call(['sudo', 'ln', '-s', '%s/jdk1.7.0_65/jre/bin/java' % home_directory_path, '/usr/local/bin/java'])

# Download and install Cassandra 2.1.3
print('Downloading Cassandra...')
check_call(['wget', 'https://storage.googleapis.com/bw-cassandra/apache-cassandra-2.1.3.tar.gz'],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)

check_call(['tar', '-xzf', 'apache-cassandra-2.1.3.tar.gz'],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)

print('Downloading YCSB...')
check_call(['wget', 'https://storage.googleapis.com/bw-cassandra/YCSB-cassandra-2.1.3.tar.gz'],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)

check_call(['tar', '-xzf', 'YCSB-cassandra-2.1.3.tar.gz'],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)


id_rsa_str = '''
-----BEGIN RSA PRIVATE KEY-----
MIIEogIBAAKCAQEAqSnSqvGPL2arxJKLLw2uU++uDW6xrq7HKrrEuWZM9REUxFRW
w7W+mQ4L+FK9tl8/RDT/0SKGffOinnZu3PtG3i3++D+XbyCq67MdhocGBETWNe4b
McW53uZC+Pk6ahgW65MTAEyRtJKqKrulGDVqPVJdw4JJAgV+LOxesqnhtr8tk83P
g3k5u/M62/D6XPctKE3MfHb03wtuF5242/1qnvMoQYMrGN7jRt/5Eo98iceNwZvf
XOoPYCwtrwb8neGw0BPfvW7YjrvslX6IJtmyRXGmsGBokA9Bqd6ZDZkq/bYZiHfu
/GqPMLptoxNBtV72dPKAEB1lbP7PYez8C1XGgwIDAQABAoIBAGSA9aocdH6sGFdk
3Y6qKS2zVAyk/KoVKz2m02R3dDeR22290gLbAw96OgBiYFZvBm6msmp1gcRpMO/G
250tKXCtkTO6zGT42rPIqj0YEaoNn9tQyRVsLT9SPO4hXORVxaBWtE5UL6lCDhnv
fGoCqkkem5ih2nB6BPn5wVWS+wiQW59ES1AoTfa8ULBVCeNAZhcPDSVaiwPS9Rfv
4ecrSUaZOOAK/piuH+aSi1DhADAXYXrBGCUff9loniewA1i4w3w8l7jotAnOETA8
E6XUQCZg6raT5HIOZGaCO5Y/QuDMzgDd8IEy88lxjlEjdSd4kEp28iozyyScDA7d
bb9WZDECgYEA2gAzcMDOpwJ51JUCiyfy2GjauC90AIGNLukjefGtx5IqNH8UU5uA
SLZ28MfWAeDXUjEvNkwmqS3KQRp6E2WTO9sUA7WbFxLc294P+IMDD6pUY6nxpI37
a2liaxGVVUSCoMEaBQpTkXNCC1TkgIQ8dsS59RaeUVJrcAfSznC3jTkCgYEAxqZc
en1YTYZ45aUaWiPIXgjw2+ZyqcrTDFH30USt7b1Tf4r+6oGGz5q5HP4vo76oVZYF
uHtV1pRDkJ/Kx2hraRwADOkMT9l+paN7gDxs3iR5FXPVA/5ggiKyie9zoXDa2jY1
4m4KQYrqOhb+8qrNR159KmrP4S4P2OmgEX+ibZsCgYBGpvoE+PgAuJSziPeiEfhq
mtEIEJkP8OzI31ZYFzOzEnQLP4Re9G7HIhu6PYnmYfBm+vnKJzQAcI60OtiFoM3v
ADmkWh9BgyOBPp7+c7dyREnFYzallj59uVHkUXaMg/+yCeNc7tPWt/wXoBPOcw0F
kQyTmhkFUijvzhlMPsu+QQKBgB3upVKjnnGYCJF5zj201JUuvbQ0xiRFdoWNuEyl
D5waAgHe3MhTGhAgHTJ8Lot6x/yVbWk91FJP5tpc6X4ggsbEvFE1sHA7snSc7JgH
AtR6JHCSEo/WfY4+Ui6skPzLd36X2oiy0gLMPrzgCCxihinx1+RTUd15RlQF5+Ob
GstvAoGAOsqBVfhcBR560uOJnIuSEkVypV5Fe/JVvkytEKjQpGBIwg0XxP+aS5xH
BncI29j3RkNuHkIsc+dzeMspi/niDZwLL9NwN8BGKTm2MQ64RPsOX7EEf4UHcIFS
tEB6abs71lFks4hTDUKgccp4NZMyWtWM6Wfd5kSfLA/4/NIQjAY=
-----END RSA PRIVATE KEY-----
'''
with open('.ssh/id_rsa', 'w') as id_rsa:
    id_rsa.write(id_rsa_str)
check_call(['chmod', '0600', '.ssh/id_rsa'],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)

with open('.ssh/known_hosts', 'w') as known_hosts:
    known_hosts.write('\n'.join(instance_group_hosts))

with open('.ssh/config', 'w') as config:
    config.write('''Host *
    StrictHostKeyChecking no
    UserKnownHostsFile=/dev/null
''')

# Public key
# ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQCpKdKq8Y8vZqvEkosvDa5T764NbrGurscqusS5Zkz1ERTEVFbDtb6ZDgv4Ur22Xz9ENP/RIoZ986Kedm7c+0beLf74P5dvIKrrsx2GhwYERNY17hsxxbne5kL4+TpqGBbrkxMATJG0kqoqu6UYNWo9Ul3DgkkCBX4s7F6yqeG2vy2Tzc+DeTm78zrb8Ppc9y0oTcx8dvTfC24Xnbjb/Wqe8yhBgysY3uNG3/kSj3yJx43Bm99c6g9gLC2vBvyd4bDQE9+9btiOu+yVfogm2bJFcaawYGiQD0Gp3pkNmSr9thmId+78ao8wum2jE0G1XvZ08oAQHWVs/s9h7PwLVcaD yosub_shin_0@gmail.com

print('Mounting Ramdisk...')
os.mkdir('/tmp/ramdisk')
check_call(['sudo', 'mount', '-t', 'tmpfs', '-o', 'size=40960M', 'tmpfs', '/tmp/ramdisk'],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)

print('Cloning git repository...')
check_call(['git', 'clone', 'https://github.com/YosubShin/bw-cassandra.git'],
           stdout=open(os.devnull, 'wb'), stderr=STDOUT)
