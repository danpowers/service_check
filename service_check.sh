#!/bin/bash

if  [ "$#" != "1" ] || [ "$1" != "--myproxy" -a "$1" != "--gridftp" ];
then
 echo Usage: $0 '[--myproxy|--gridftp]'
 exit 0
fi

while :
do
 echo $(date -u) Starting \"service_check.py $1\"
 ./service_check.py $1
 sleep 5
done
