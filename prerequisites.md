# PiERS Prerequisites

sudo apt update
sudo apt full-upgrade -y 
sudo apt install git -y 
sudo raspi-config nonint do_change_locale en_US.UTF-8
reboot

git clone https://github.com/k7ctc/piers-beta /home/pi/git/piers
cd git/piers
sudo ./node_setup.sh [station id integer]