#!/bin/bash
# !/bin/bash -x to turn echo on

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd ${DIR}

source ../env/bin/activate
python syncWebServer.py http://ec2-52-56-214-201.eu-west-2.compute.amazonaws.com:8001&