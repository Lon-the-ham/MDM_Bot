#!/bin/bash
source /home/pi/.bashrc
date >> /home/pi/bots/MDM_Bot/logs/yata_startlog.txt
cd /home/pi/bots/MDM_Bot
/bin/python /home/pi/bots/MDM_Bot/other/rebootmessenger.py
pkill -9 -f mdmbot.py
sleep 10
/bin/python /home/pi/bots/MDM_Bot/mdmbot.py
