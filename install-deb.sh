#!/bin/bash
sudo apt update
sudo apt -y upgrade
sudo apt-get install -y zlib1g-dev
sudo apt install -y python3
sudo apt install -y python3-pip
python3 -m pip install --upgrade pip
sudo apt-get install -y libgtk-3-dev
sudo apt-get install -y python3-gi
sudo apt-get install -y zlib1g
sudo apt-get install -y python3-distutils
pip3 install -r requirements.txt
