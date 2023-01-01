#!/bin/bash

PROCESS="python3 /home/pi/AirQmonitor/AirQmonitorSEN.py"
PIDOF="/usr/bin/pidof"
KILL="/usr/bin/kill"
AQ="su - pi -c '/home/pi/AirQmonitor/AirQmonitorSEN.py'"

RUN=`$PIDOF $PROCESS`
# >/dev/null`

if [ $? != 0 ]; then
  echo "Start AirQmonitor"
  /home/pi/pushover.sh "AirQmonitor.py RESTART"
  $AQ
else
  echo "Save VOC algo state"
  $KILL -SIGUSR2 $RUN
fi
