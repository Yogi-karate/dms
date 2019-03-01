#!/bin/bash        
set -e
docker stop $1
docker rm $1
docker build . -t tramm/$1
docker run -d -p 8069:8069 --name $1 tramm/$1

