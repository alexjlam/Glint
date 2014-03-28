#!/bin/bash

export EC2_HOME=/usr/local/ec2/ec2-api-tools-1.6.12.2
export PATH=$PATH:$EC2_HOME/bin
export EC2_AMITOOL_HOME=/usr/local/ec2/ec2-ami-tools-1.5.2
export PATH=$EC2_AMITOOL_HOME/bin:$PATH
export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64/jre

# not required when runnning server
#export AWS_ACCESS_KEY=
#export AWS_SECRET_KEY=
#export AWS_ACCOUNT_NUMBER=
#export EC2_URL=
