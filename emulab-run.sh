#!/bin/bash

# Copy ssh keys and public keys so that root user can freely login to other nodes without prompted for password
parallel-ssh -h /tmp/hosts 'sudo bash -c "cp /users/yossupp/.ssh/id_rsa /root/.ssh/;cat /users/yossupp/.ssh/authorized_keys >> /root/.ssh/authorized_keys"'

sudo -u root bash <<EOF

# Updating maximum opened file descriptor limit
ulimit -n 32768

# Execute coordinator with emulab profile
python /proj/ISS/shin14/bw-cassandra/bw-cassandra/coordinator.py emulab

EOF