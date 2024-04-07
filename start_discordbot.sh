#!/bin/bash
source ~/.bashrc
BASEDIR=$(dirname "$0")
cd "$BASEDIR"
/usr/bin/python3 "$BASEDIR/other/rebootmessenger.py"
pkill -9 -f mdmbot.py
sleep 10
/usr/bin/python3 "$BASEDIR/mdmbot.py"
