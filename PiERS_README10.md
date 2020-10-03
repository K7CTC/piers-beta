# Raspberry Pi Event Reporting System (PiERS)

PiERS (pronounced "peers") facilitates tracking and reporting of participant status through the duration of an ultra marathon style event where traditional communication methods are unviable.  This is accomplished through a combination of purpose built software running on a Raspberry Pi single board computer paired with a wireless transceiver.  Logging of participant status (active, did not start, did not finish, etc.) along with an accurate timestamp and location data is performed via a web interface and stored locally on the Raspberry Pi.  These log entries are then transmitted via the attached transciver to all other stations listening on the same frequency and mode.

The end result is what can be described as an ad-hoc mesh network arrangement of stations (representing specific locations along a predefined route) beaconing the status of event paricipants (identified by bib number) as they progress through a course, from start to finish.  All stations within the network can therefore accumulate participant details in real time.  This data is stored in a database local to the Raspberry Pi and can be queried against should the need arise (as it often does).

## Required Hardware

* [Raspberry Pi 3 B+](https://www.raspberrypi.org/products/raspberry-pi-3-model-b-plus)
* Suitable microSD card (SanDisk Ultra or Extreme recommended)
* Suitable USB flash drive (for storing event data)
* Suitable USB audio adapter (if using Dire Wolf as a TNC for VHF packet operation)
* Suitable USB to serial adapter (if using an external TNC or if using Dire Wolf with a radio lacking VOX)
* [RONOTH LoStik](https://ronoth.com/lostik) (if using LoRa for data TX/RX)
* Suitable Raspberry Pi power source and cable (2.5A @ 5VDC)

## Recommended Hardware

### Powering Your Pi

* [Powerwerx USBbuddy Powerpole to USB (3A @ 5VDC)](https://powerwerx.com/usbbuddy-powerpole-usb-converter-device-charger)
* [Anker PowerCore Lite 10000mAh](https://www.amazon.com/Anker-PowerCore-Ultra-Compact-High-Speed-Technology/dp/B0194WDVHI/ref=sr_1_3?keywords=Anker%2BPowerCore&qid=1582742814&sr=8-3&th=1)
* Micro USB cable capable of delivering up to 3A @ 5VDC

### Running Your Pi

* [SanDisk Ultra microSD Card](https://www.amazon.com/gp/product/B073JWXGNT/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)
* [Kingston DTSE9 16GB USB Drive](https://www.amazon.com/Kingston-Digital-DataTraveler-DTSE9H-16GBZ/dp/B006W8U2WU)
* [Enokay Case for Raspberry Pi 3 B+](https://www.amazon.com/gp/product/B07B655H6J/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1)

### Transceiver Interface

* [TigerTronics SignaLink USB](https://www.tigertronics.com)
* [Plugable USB Audio Adapter](https://plugable.com/products/usb-audio)
* [GearMo 12" USB to RS232 Serial Adapter FTDI Chip](https://www.gearmo.com/shop/12-inch-usb-to-rs232-serial-adapter-ftdi-chip)
* [Tera Grand USB to RS232 Serial Adapter FTDI Chip](https://www.amazon.com/gp/product/B00BUZ0K68/ref=ppx_yo_dt_b_search_asin_title?ie=UTF8&psc=1)

## What install.sh Does

The Raspberry Pi Event Reporting System installation script automates the process of provisioning the Pi as a PiERS node (station).  Execution of install.sh performs the following steps:

* Processing of command line argument (station id)
* Checks to see if user is running as root (administrator)
* Checks to see if install.sh has been previously executed
* Checks connectivity to raspbian.raspberrypi.org and github.com
* Performs required PiERS installation steps
  * Geterates a log file: /home/pi/git/k7ctc/piers/install.log (collects all STDERR and STDOUT)
  * Changes system keyboard layout to United States (US)
  * Updates system package list
  * Installs all available system updates
  * Installs required packages (apache2 php7.3 php7.3-sqlite3 python3-serial sqlite3)
  * Enables SSH
  * Generates MOTD for SSH logins
  * Generates a custom /boot/config.txt
    * Disables onboard audio hardware
    * Disables onboard bluetooth hardware
  * Installs and configures the web application
  * Clones the appropriate piers-event repository
  * Clones the piers-lostik repository
* Installs and configures the hotspot (access point) if SETAP variable is set to "true"
  * Installs required packages (dnsmasq @ hostapd)
  * Stops installed services (while we do some work on the configuration files)
  * Appends /etc/dhcpcd.conf (IP configuration)
    * Sets the static IP address for wlan0 to 10.0.5.1
    * Sets nohook for wpa_supplicant
  * Generates /etc/dnsmasq.conf (DHCP configuration)
    * Sets IP address lease range from 10.0.5.2 to 10.0.5.20 for wlan0
    * Sets IP address lease time to 48 hours for wlan0
  * Generates /etc/hostapd/hostapd.conf (AP configuration)
    * Targets wlan0 with appropriate driver (onboard WiFi interface)
    * Sets device SSID to PiERS
    * Sets WiFi country code to US
    * Sets WiFi radio to channel 6
    * Sets WPA2 passphrase
  * Generates /etc/default/hostapd
    * Sets location of configuration file
  * Unmasks the installed services (dnsmasq & hostapd)
  * Enables the installed services (dnsmasq & hostapd)
  * Starts the installed services (dnsmasq & hostapd)
* Sets the hostname to the value specified in the SETHOSTNAME variable
* Instructs user to shutdown via "shutdown now" command

## Quick Start

Once you have booted a fresh Raspbian Buster Lite (2020-02-13) image on your Pi and established a wired internet connection, simply enter the following keystrokes to setup your PiERS node:

```bash
pi [enter]
raspberry [enter]
sudo apt update [enter]
sudo apt full-upgrade -y [enter]
sudo apt install git -y [enter]
sudo raspi-config nonint do_change_locale en_US.UTF-8 [enter]
reboot [enter]

{wait for Pi to reboot}

pi [enter]
raspberry [enter]
git clone https://github.com/k7ctc/piers-old /home/pi/git/k7ctc/piers [enter]
cd git/k7ctc/piers [enter]
sudo ./install [enter]
```

For production use, or if your Pi is connected to the internet, it is STRONGLY recommended that you also change the default password for the pi account (raspberry) to something more secure.  This is easily accomplished by entering the following command:

```bash
passwd
```

## Core Operating System Dependencies

The following Debian packages are required for proper compilation and operation of PiERS.  The PiERS setup script will automatically install them as well as any related package dependencies.  They are listed here for reference.

* [apache2](https://httpd.apache.org)
* [php7.3](https://php.net)
* [php7.3-sqlite3](https://www.php.net/manual/en/book.sqlite.php)
* [python3-serial](https://pyserial.readthedocs.io/en/latest)
* [sqlite3](https://sqlite.org)
* [dnsmasq](http://thekelleys.org.uk/dnsmasq/doc.html)
* [hostapd](https://w1.fi/hostapd)

## Other Dependencies

* [phpLiteAdmin v1.9.8.2](https://phpliteadmin.org)
* [w3.css v4.13 (June 2019)](https://www.w3schools.com/w3css/default.asp)
* [w3.js v1.04 (April 2019)](https://www.w3schools.com/w3js/default.asp)
* [jQuery v3.4.1](https://jquery.com/)
* [Moment.js v2.24.0](https://w3schools.com)
* [Font Awesome v5.12.1](https://fontawesome.com/)

## Developed By

* **Chris Clement (K7CTC)** - [https://qrz.com/db/K7CTC](https://qrz.com/db/K7CTC)

## License

This project is licensed under the MIT License - see [LICENSE.md](LICENSE.md) for details

## Acknowledgments

* Jason Peterson (K7EM)
* Kevin Reeve (N7RXE)
* Cordell Smart (KE7IK)
* Tyler Griffiths (N7UWX)
* Ronoth (An IoT Solutions Company)
