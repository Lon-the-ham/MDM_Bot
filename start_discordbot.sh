#!/bin/bash
source /home/pi4b/.bashrc
cd /home/pi4b/bots/MDM_Bot_v3
/bin/python /home/pi4b/bots/MDM_Bot_v3/other/rebootmessenger.py
pkill -9 -f mdmbot.py
sleep 10
/bin/python /home/pi4b/bots/MDM_Bot_v3/mdmbot.py
