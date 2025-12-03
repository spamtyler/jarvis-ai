#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=$HOME/.Xauthority
cd /mnt/fast_data/projects/vision_agent/vision_agent
./venv/bin/python3 server.py
