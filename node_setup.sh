#!/bin/bash

###########################################################
#                                                         #
#          TITLE: PiERS - Node Setup                      #
#   DEVELOPED BY: Chris Clement (K7CTC)                   #
#    DESCRIPTION: Converts a stock 2020-08-20 Raspberry   #
#                 Pi OS Lite image into a PiERS node.     #
#                                                         #
###########################################################

VERSION="v2020-08-20"
SETSTATIONID="00"
SETAP="false"

#piers setup requires root privileges 
#check to make sure user has executed the script via sudo
if [ "`whoami`" != "root" ]
then
    #inform user that they must run the command as root
    echo "  ERROR: Invalid command syntax. node_setup.sh requires root priveleges."
    echo "  USAGE: sudo ./node_setup.sh [required station id]"
    echo "   HELP: Station ID is specified as an integer between 01 and 99."
    echo
    echo "EXAMPLE: sudo ./node_setup.sh 03"
    echo
    exit 1
fi

#verify correct number of command line arguments have been provided
if [ $# -ne 1 ]
then
    echo "  ERROR: Invalid command syntax. Unexpected number of arguments."
    echo "  USAGE: sudo ./node_setup.sh [required station id]"
    echo "   HELP: Station ID is specified as an integer between 01 and 99."
    echo
    echo "EXAMPLE: sudo ./node_setup.sh 03"
    echo
    exit 1
fi

#process station id argument
if [ $1 -gt 0 ] && [ $1 -lt 100 ]
then
    #store station id argument in global station id variable
    SETSTATIONID=$1
else
    #inform user that the station id is invalid
    echo "  ERROR: Invalid command syntax. Unexpected Station ID value."
    echo "  USAGE: sudo ./node_setup.sh [required station id]"
    echo "   HELP: Station ID is specified as an integer between 01 and 99."
    echo
    echo "EXAMPLE: sudo ./node_setup.sh 03"
    echo
    exit 1
fi

#check connectivity to raspbian.raspberrypi.org (needed to obtain required packages)
ping raspbian.raspberrypi.org -c 1 &>> /dev/null
if [ $? != 0 ]
then
    echo "Unable to communicate with raspbian.raspberrypi.org at this time."
    echo "Please check your network connection and try again."
    exit 1
fi

#check connectivity to github.com (we'll need this server to obtain required resources)
ping github.com -c 1 &>> /dev/null
if [ $? != 0 ]
then
    echo "Unable to communicate with github.com at this time."
    echo "Please check your network connection and try again."
    exit 1
fi

#function: required PiERS installation steps
function installBase {
    clear
    echo "Raspberry Pi Event Reporting System - Node Setup" $VERSION
    echo "════════════════════════════════════════════════════════════"

    #change keyboard layout to US
    echo "Changing keyboard layout to United States via raspi-config..."
    sudo raspi-config nonint do_configure_keyboard us &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi
    
    #change timezone to America/Denver (MST/MDT)
    echo "Changing time zone to America/Denver (MST/MDT) via timedatectl..."
    sudo timedatectl set-timezone America/Denver &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    #install required packages
    echo "Installing required packages..."
    echo "    *i2c-tools"
    echo "    *ufw"
    echo "    *sqlite3"
    echo "    *python3-smbus"
    echo "    *python3-serial"
    # echo "    *apache2"
    # echo "    *php7.3"
    # echo "    *php7.3-sqlite3"
    sudo apt-get install -y i2c-tools ufw sqlite3 python3-smbus python3-serial &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    #configure firewall
    echo "Configuring firewall..."
    echo "    *allow SSH"
    echo "    *enable firewall on boot"
    sudo ufw allow ssh &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi
    sudo ufw enable &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    #generate SSH login message of the day (motd)
    echo "Generating: /etc/motd..."
    sudo echo > /etc/motd
    sudo echo "╔═════════════════════════════════════════════════╗" >> /etc/motd
    sudo echo "║    ______    _   _______   ______     ______    ║" >> /etc/motd
    sudo echo "║   (_____ \  (_) (_______) (_____ \   / _____)   ║" >> /etc/motd
    sudo echo "║    _____) )  _   _____     _____) ) ( (____     ║" >> /etc/motd
    sudo echo "║   |  ____/  | | |  ___)   |  __  /   \____ \    ║" >> /etc/motd
    sudo echo "║   | |       | | | |_____  | |  \ \   _____) )   ║" >> /etc/motd
    sudo echo "║   |_|       |_| |_______) |_|   |_| (______/    ║" >> /etc/motd
    sudo echo "║                                                 ║" >> /etc/motd
    sudo echo "╚═══════╡ https://github.com/k7ctc/piers ╞════════╝" >> /etc/motd
    sudo echo >> /etc/motd
    sudo echo "Welcome to the Raspberry Pi Event Reporting System!" >> /etc/motd
    sudo echo "Enjoy your stay..." >> /etc/motd
    sudo echo >> /etc/motd

    #generate /boot/config.txt
    echo "Generating: /boot/config.txt..."
    echo "    *Disabling onboard audio..."
    echo "    *Disabling onboard bluetooth..."
    echo "    *Forcing HDMI hotplug..."
    echo "    *Forcing HDMI mode: 720p"       
    sudo echo "#/boot/config.txt generated by PiERS installation script" $VERSION > /boot/config.txt
    sudo echo >> /boot/config.txt
    sudo echo "#additional options and information can be obtained here:" >> /boot/config.txt
    sudo echo "#https://www.raspberrypi.org/documentation/configuration/config-txt/README.md" >> /boot/config.txt
    sudo echo "#NOTE: Some settings impact device functionality, see above link for details." >> /boot/config.txt
    sudo echo >> /boot/config.txt
    sudo echo "#force HDMI output settings" >> /boot/config.txt
    sudo echo "hdmi_force_hotplug=1" >> /boot/config.txt
    sudo echo "hdmi_group=2" >> /boot/config.txt
    sudo echo "hdmi_mode=85" >> /boot/config.txt
    sudo echo "disable_overscan=0" >> /boot/config.txt
    sudo echo >> /boot/config.txt
    sudo echo "#disable onboard audio" >> /boot/config.txt
    sudo echo "dtparam=audio=off" >> /boot/config.txt
    sudo echo >> /boot/config.txt
    sudo echo "#disable onboard bluetooth" >> /boot/config.txt
    sudo echo "dtoverlay=disable-bt" >> /boot/config.txt
    sudo echo >> /boot/config.txt
    sudo echo "#disable onboard wlan0 (uncomment if desired)" >> /boot/config.txt
    sudo echo "#dtoverlay=disable-wifi" >> /boot/config.txt
    sudo echo >> /boot/config.txt
    sudo echo "#enable Adafruit PiRTC" >> /boot/config.txt
    sudo echo "dtoverlay=i2c-rtc,ds3231" >> /boot/config.txt

    #enable SSH
    echo "Enabling SSH via raspi-config..."
    sudo raspi-config nonint do_ssh 0 &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    #enable I2C
    echo "Enabling I2C via raspi-config..."
    sudo raspi-config nonint do_i2c 0 &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    # #add user pi as a member of the www-data group
    # echo "Adding user \"pi\" as a member of group \"www-data\"..."
    # echo "Adding user \"pi\" as a member of group \"www-data\"" >> /home/pi/git/k7ctc/piers/install.log
    # sudo usermod -a -G www-data pi &>> /home/pi/git/k7ctc/piers/install.log
    
    # #add user www-data as a member of the pi group
    # echo "Adding user \"www-data\" as a member of group \"pi\"..."
    # echo "Adding user \"www-data\" as a member of group \"pi\"" >> /home/pi/git/k7ctc/piers/install.log
    # sudo usermod -a -G pi www-data &>> /home/pi/git/k7ctc/piers/install.log
    
    # #ensure user www-data can execute /bin/date
    # echo "Allowing user \"www-data\" to execute /bin/date..."
    # echo "Allowing user \"www-data\" to execute /bin/date" >> /home/pi/git/k7ctc/piers/install.log
    # sudo chmod -v u+s /bin/date &>> /home/pi/git/k7ctc/piers/install.log

    # #install and configure web interface
    # echo "Installing PiERS web interface..."
    # echo "Installing PiERS web interface" >> /home/pi/git/k7ctc/piers/install.log
    # sudo rm -rf /var/www/html &>> /home/pi/git/k7ctc/piers/install.log
    # sudo cp -R /home/pi/git/k7ctc/piers/web /var/www/html &>> /home/pi/git/k7ctc/piers/install.log
    # sudo chown -v -R www-data:www-data /var/www/* &>> /home/pi/git/k7ctc/piers/install.log
    # sudo chmod -v -R g+w /var/www/* &>> /home/pi/git/k7ctc/piers/install.log

    # #pull down the PiERS default event repository
    # echo "Installing PiERS event definition module..."
    # echo "Installing PiERS event definition module" >> /home/pi/git/k7ctc/piers/install.log
    # git clone https://github.com/k7ctc/piers-event-$SETEVENT /home/pi/event &>> /home/pi/git/k7ctc/piers/install.log
    # sudo chown -v -R pi:pi /home/pi/event &>> /home/pi/git/k7ctc/piers/install.log    

    # #pull down the Ronoth LoStik PiERS module
    # echo "Installing Ronoth LoStik PiERS module..."
    # echo "Installing Ronoth LoStik PiERS module" >> /home/pi/git/k7ctc/piers/install.log
    # git clone https://github.com/k7ctc/piers-lostik /home/pi/lostik &>> /home/pi/git/k7ctc/piers/install.log
    # sudo chown -v -R pi:pi /home/pi/lostik &>> /home/pi/git/k7ctc/piers/install.log

    #establish config file (set station id)
    echo "Generating: /home/pi/piers.conf..."
    echo $SETSTATIONID > /home/pi/piers.conf
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    #copy piers application files into home directory
    echo "Installing PiERS..."
    cp /home/pi/git/piers/*.py /home/pi/
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi
    cp /home/pi/git/piers/*.csv /home/pi/
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi
    sudo chown pi:pi /home/pi/* &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi
    sudo chmod +x /home/pi/*.py &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi
}

#function: configures PiERS node as a WiFi access point (AP)
function installAP {
    echo "Installing required packages..."
    echo "    *dnsmasq"
    echo "    *hostapd"
    sudo apt-get install -y dnsmasq hostapd &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    echo "Stopping dnsmasq service..."
    sudo systemctl stop dnsmasq &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    echo "Stopping hostapd service..."
    sudo systemctl stop hostapd &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    echo "Appending new IP configuration for interface wlan0 to /etc/dhcpcd.conf..."
    sudo echo "interface wlan0" >> /etc/dhcpcd.conf
    sudo echo "    static ip_address=10.0.5.1/24" >> /etc/dhcpcd.conf
    sudo echo "    nohook wpa_supplicant" >> /etc/dhcpcd.conf

    echo "Generating: /etc/dnsmasq.conf..."
    sudo echo "interface=wlan0" > /etc/dnsmasq.conf
    sudo echo "    dhcp-range=10.0.5.2,10.0.5.20,255.255.255.0,48h" >> /etc/dnsmasq.conf

    echo "Generating: /etc/hostapd/hostapd.conf..."
    sudo echo "interface=wlan0" > /etc/hostapd/hostapd.conf
    sudo echo "driver=nl80211" >> /etc/hostapd/hostapd.conf
    sudo echo "ssid=PiERS" >> /etc/hostapd/hostapd.conf
    sudo echo "country_code=US" >> /etc/hostapd/hostapd.conf
    sudo echo "hw_mode=g" >> /etc/hostapd/hostapd.conf
    sudo echo "channel=6" >> /etc/hostapd/hostapd.conf
    sudo echo "macaddr_acl=0" >> /etc/hostapd/hostapd.conf
    sudo echo "auth_algs=1" >> /etc/hostapd/hostapd.conf
    sudo echo "ignore_broadcast_ssid=0" >> /etc/hostapd/hostapd.conf
    sudo echo "wpa=2" >> /etc/hostapd/hostapd.conf
    sudo echo "wpa_passphrase=barconline" >> /etc/hostapd/hostapd.conf
    sudo echo "wpa_key_mgmt=WPA-PSK" >> /etc/hostapd/hostapd.conf
    sudo echo "wpa_pairwise=TKIP" >> /etc/hostapd/hostapd.conf
    sudo echo "rsn_pairwise=CCMP" >> /etc/hostapd/hostapd.conf

    echo "Generating: /etc/default/hostapd..."
    sudo echo DAEMON_CONF=\"/etc/hostapd/hostapd.conf\" > /etc/default/hostapd

    echo "Unmasking dnsmasq service..."
    sudo systemctl unmask dnsmasq &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    echo "Unmasking hostapd service..."
    sudo systemctl unmask hostapd &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    echo "Enabling dnsmasq service..."
    sudo systemctl enable dnsmasq &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    echo "Enabling hostapd service..."
    sudo systemctl enable hostapd &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    echo "Starting dnsmasq service..."
    sudo systemctl start dnsmasq &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    echo "Starting hostapd service..."
    sudo systemctl start hostapd &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi
}

#function: final information upon exit
function finish {
    #it's important that the hostname is the last system modification made by PiERS install
    #otherwise other steps will fail to execute.  that's why it's way down here with the
    #finish function.
    echo "Changing hostname to PiERS via raspi-config..."
    sudo raspi-config nonint do_hostname PiERS &>> /dev/null
    if [ $? != 0 ]
    then
        echo "FAILURE!"
        exit 1
    fi

    echo
    echo "Finished!"
    echo "════════════════════════════════════════════════════════════"
    echo "It is recommended that you shutdown your PiERS node at this time and"
    echo "configure your hardware before next boot.  You can shutdown with the"
    echo "following command:"
    echo
    echo "shutdown now"
    echo
    exit 0
}

#script logic
installBase
if [ $SETAP = "true" ]
then
    installAP
fi
finish
exit 1
