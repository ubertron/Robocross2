#!/bin/bash
cd ~/Dropbox/Technology/Python3/Projects/Robocross2 || exit
export PYTHONPATH=$PYTHONPATH:~/Dropbox/Technology/Python3/Projects/Robocross2
source .venv/bin/activate
.venv/bin/python3 robocross/robocross_ui.py