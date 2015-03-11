#!/bin/bash
# DATE       AUTHOR      COMMENT
# ---------- ----------- -----------------------------------------------------
# 2015-03-04 Yosub Shin  Initial Version

BASE_PATH=/u/sciteam/shin1/scratch
JAVA_INSTALL_DIR=jdk1.7.0_65
JAVA_INSTALL_FILE=jdk-7u65-linux-x64.tar.gz


if ! [ -f "$JAVA_INSTALL_PATH" ]
then
    echo "Java install file does not exists"
    wget --directory-prefix=$BASE_PATH --output-document=$BASE_PATH/$JAVA_INSTALL_FILE --no-check-certificate --no-cookies --header "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/7u65-b17/$JAVA_INSTALL_FILE
else
    echo "Java install file already exists."
fi
tar -xvf $BASE_PATH/$JAVA_INSTALL_FILE -C $BASE_PATH


JAVA_HOME=$BASE_PATH/$JAVA_INSTALL_DIR


#Install YCSB
wget https://github.com/downloads/brianfrankcooper/YCSB/ycsb-0.1.4.tar.gz