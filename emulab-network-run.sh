#!/bin/bash

cat /etc/hosts | grep node | awk '{print $4}' > /tmp/hosts

parallel-ssh -i -h /tmp/hosts -I sudo bash <<EOF

# Copy ssh keys and public keys so that root user can freely login to other nodes without prompted for password
if [ "`sudo cat /root/.ssh/authorized_keys | wc -l`" -lt "10" ]; then
cp /users/yossupp/.ssh/id_rsa /root/.ssh/
cat /users/yossupp/.ssh/authorized_keys >> /root/.ssh/authorized_keys
fi

EOF


sudo -u root bash <<EOF

# Updating maximum opened file descriptor limit
ulimit -n 32768

# Execute coordinator with emulab profile
python /proj/ISS/shin14/bw-cassandra/bw-cassandra/coordinator.py emulab 2>&1 | tee /tmp/stdout

EOF