# PiERS Installation

## Keystrokes:

```bash
pi [enter]
raspberry [enter]
sudo raspi-config [enter]
[enter]
[enter]
(password) [enter]
(password) [enter]
[enter]
[down arrow] [enter]
[down arrow] [enter]
u [down arrow] [down arrow] [down arrow] [enter]
[enter]
(SSID) [enter]
(passphrase) [enter]
[tab] [tab] [enter]
```

{wait about 15 seconds for wifi to connect}

```bash
sudo apt update [enter]
sudo apt full-upgrade -y [enter]
sudo apt install git -y [enter]
sudo raspi-config nonint do_change_locale en_US.UTF-8 [enter]
reboot [enter]

pi [enter]
(password) [enter]
git clone https://github.com/k7ctc/piers-old /home/pi/git/k7ctc/piers [enter]
cd git/k7ctc/piers [enter]
sudo ./install [enter]
```
