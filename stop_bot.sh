#!/bin/bash
source ~/.bashrc
BASEDIR=$(dirname "$0")
cd "$BASEDIR"
pkill -9 -f mdmbot.py
