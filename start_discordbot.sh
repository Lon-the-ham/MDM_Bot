#!/bin/bash
source /home/pi/.bashrc
date >> /home/pi/bots/mdm/yata/logs/yata_startlog.txt
cd /home/pi/bots/mdm/yata
/bin/python /home/pi/bots/mdm/yata/other/rebootmessenger.py
pkill -9 -f mdmbot.py
sleep 10
/bin/python /home/pi/bots/mdm/yata/mdmbot.py
