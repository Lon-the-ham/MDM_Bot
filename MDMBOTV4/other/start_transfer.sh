#!/bin/bash
source ~/.bashrc
BASEDIR=$(dirname "$0")
cd "$BASEDIR"
/usr/bin/python3 "$BASEDIR/transfer_v3_to_v4.py"
