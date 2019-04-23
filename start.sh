#!/bin/bash
# !/bin/bash -x to turn echo on

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
cd ${DIR}

source ../env/bin/activate
python syncWebServer.py http://ec2-52-56-214-201.eu-west-2.compute.amazonaws.com:8001 &
VIBORA_PID=$!

# Create a stop.sh script to kill the running instances
echo "#!/bin/bash" > stop.sh
chmod +x stop.sh
echo "# this script is automatically created - from start.sh"
echo "kill -9 ${VIBORA_PID}" >> stop.sh
echo "***********************"
echo "run ${DIR}/stop.sh to stop the servers"