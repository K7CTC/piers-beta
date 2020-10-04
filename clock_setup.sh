#!/bin/bash

###########################################################
#                                                         #
#          TITLE: PiERS - Clock Setup                     #
#   DEVELOPED BY: Chris Clement (K7CTC)                   #
#    DESCRIPTION: Configures 2020-08-20 Raspberry Pi OS   #
#                 to utilize an attached Adafruit PiRTC   #
#                 DS3231 for precise timekeeping.         #
#                                                         #
###########################################################

#piers setup requires root privileges 
#check to make sure user has executed the script via sudo
if [ "`whoami`" != "root" ]
then
    #inform user that they must run the command as root
    echo "  ERROR: Invalid command syntax. clock_setup.sh requires root priveleges."
    echo "  USAGE: sudo ./clock_setup.sh"
    echo
    exit 1
fi

#check connectivity to pool.ntp.org (needed to obtain correct time)
ping pool.ntp.org -c 1 &>> /dev/null
if [ $? != 0 ]
then
    echo "Unable to communicate with pool.ntp.org at this time."
    echo "Please check your network connection and try again."
    exit 1
fi

#disable fake-hwclock package
echo "Disabling fake-hwclock..."
sudo apt-get remove fake-hwclock -y &>> /dev/null
if [ $? != 0 ]
then
    echo "FAILURE!"
    exit 1
fi
sudo update-rc.d -f fake-hwclock remove &>> /dev/null
if [ $? != 0 ]
then
    echo "FAILURE!"
    exit 1
fi
sudo systemctl disable fake-hwclock &>> /dev/null
if [ $? != 0 ]
then
    echo "FAILURE!"
    exit 1
fi

#rewrite /lib/udev/hwclock-set
echo "Generating: /lib/udev/hwclock-set..."
sudo echo "#!/bin/sh" > /lib/udev/hwclock-set
sudo echo >> /lib/udev/hwclock-set
sudo echo "if [ -e /run/udev/hwclock-set ] ; then" >> /lib/udev/hwclock-set
sudo echo "    exit 0" >> /lib/udev/hwclock-set
sudo echo "fi" >> /lib/udev/hwclock-set
sudo echo >> /lib/udev/hwclock-set
sudo echo "if [ -f /etc/default/rcS ] ; then" >> /lib/udev/hwclock-set
sudo echo "    . /etc/default/rcS" >> /lib/udev/hwclock-set
sudo echo "fi" >> /lib/udev/hwclock-set
sudo echo >> /lib/udev/hwclock-set
sudo echo "if [ -f /etc/default/hwclock ] ; then" >> /lib/udev/hwclock-set
sudo echo "    . /etc/default/hwclock" >> /lib/udev/hwclock-set
sudo echo "fi" >> /lib/udev/hwclock-set
sudo echo >> /lib/udev/hwclock-set
sudo echo "/sbin/hwclock --hctosys" >> /lib/udev/hwclock-set
sudo echo >> /lib/udev/hwclock-set
sudo echo "> /run/udev/hwclock-set" >> /lib/udev/hwclock-set
sudo echo >> /lib/udev/hwclock-set

#set PiRTC time
echo "Setting time on PiRTC based on current system time..."
sudo hwclock -w &>> /dev/null
if [ $? != 0 ]
then
    echo "FAILURE!"
    exit 1
fi

echo "Calling: timedatectl..."
sudo timedatectl

exit 0
