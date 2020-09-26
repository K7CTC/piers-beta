########################################################################
#                                                                      #
#          NAME:  PiERS - LoStik                                       #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                #
#       VERSION:  v0.2                                                 #
#      LOCATION:  /home/pi/lostik.py                                   #
#   DESCRIPTION:  The purpose of this script is to interface the PiERS #
#                 database with the Ronoth LoStik.  It is responsible  #
#                 for depositing received packets into the database as #
#                 well as transmitting queued packets and updating     #
#                 the record reflecting each successful transmission.  #
#                                                                      #
########################################################################

import logging
import subprocess
import argparse
import datetime
import os
import serial
import serial.tools.list_ports
import sqlite3
import sys
import time
import atexit
from pathlib import Path

logging.basicConfig(filename='lostik.log',
                    format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S %p',
                    level=logging.INFO)

parser = argparse.ArgumentParser(description='PiERS Module - Ronoth LoStik',
                                 epilog='Created by K7CTC. The purpose of this script is to '
                                 'interface the PiERS database with the Ronoth LoStik.  It is '
                                 'responsible for depositing received packets into the database '
                                 'as well as transmitting queued packets and updating the record '
                                 'reflecting each successful transmission.')
parser.add_argument('--pwr',
                    type=int,
                    choices=range(2, 21),
                    help='LoStik transmit power. (range: 2 to 20 - default: 2)',
                    default='2')
parser.add_argument('--cr',
                    type=int,
                    choices=range(5, 9),
                    help='LoStik coding rate. (values: 5, 6, 7, 8 - default: 5)',
                    default='5')
parser.add_argument('--wdt',
                    type=int,
                    choices=range(0,61),
                    help='LoStik watchdog timer time-out in seconds. '
                    '(range: 0 to 60, default: 5)',
                    default='5')
args = parser.parse_args()

#convert wdt from seconds to milliseconds before proceeding
args.wdt = args.wdt * 1000

#global variables
version = 'v0.2'
lostik = None
lostik_port = None

logging.info('-------------------------------------------------------------------------------')
logging.info('lostik.py %s started', version)

#lostik PiERS network variables (all nodes must share the same settings)
#Frequency (hardware default=923300000)
#value range: 902000000 to 928000000
set_freq = b'923300000'
#Modulation Mode (hardware default=lora)
#this exists just in case the radio was somehow mistakenly set to FSK
set_mod = b'lora'
#CRC Header (hardware default=on)
#values: on, off (not sure what this does, best to use default value)
set_crc = b'on'
#IQ Inversion (hardware default=off)
#values: on, off (not sure what this does, best to use default value)
set_iqi = b'off'
#Sync Word (hardware default=34)
#value: one hexadecimal byte
set_sync = b'34'
#Spreading Factor (hardware default=sf12)
#values: sf7, sf8, sf9, sf10, sf11, sf12
set_sf = b'sf12'
#Radio Bandwidth (hardware default=125)
#values: 125, 250, 500
set_bw = b'125'

#lostik PiERS node variables (can vary from one node to the next based on operating conditions)
#Transmit Power (hardware default=2)
#value range: 2 to 20
set_pwr = bytes(str(args.pwr), 'ASCII')
#Coding Rate (hardware default=4/5)
#values: 4/5, 4/6, 4/7, 4/8
set_cr = b''.join([b'4/', bytes(str(args.cr), 'ASCII')])
#Watchdog Timer Time-Out (hardware default=15000, script default=5000)
#value range: 0 to 4294967295 (0 disables wdt functionality)
set_wdt = bytes(str(args.wdt), 'ASCII')

#verify existence of PiERS database before proceeding
if Path('piers.sqlite3').is_file() == False:
    print('ERROR: File not found - piers.sqlite3')
    logging.error('File not found - piers.sqlite3')
    sys.exit(1)

########################################################################
# LoStik Notes:  The Ronoth LoStik USB to serial device has a VID:PID  #
#                equal to 1A86:7523.  Using pySerial we are able to    #
#                query the system (Windows/Linux/macOS) to see if a    #
#                device matching this VID:PID is attached via USB.  If #
#                a LoStik is detected, we can then assign its port     #
#                programmatically.  This eliminates the need to        #
#                guess the port or obtain it as a command line         #
#                argument.  This only took several months to figure    #
#                out.                                                  #
########################################################################

#attempt LoStik detection and port assignment
lostik_port = None
ports = serial.tools.list_ports.grep('1A86:7523')
for port in ports:
    lostik_port = port.device
    logging.info('LoStik detected on port: ' + lostik_port)
if lostik_port == None:
    print('ERROR: LoStik not detected!')
    logging.error('LoStik not detected!')
    print('HELP: Check serial port descriptor and/or device connection.')
    logging.info('Check serial port descriptor and/or device connection.')
    sys.exit(1)

#attempt LoStik connection
try:
    lostik = serial.Serial(lostik_port, baudrate=57600, timeout=1)
except:
    print('ERROR: Unable to connect to LoStik!')
    logging.error('Unable to connect to LoStik!')
    print('HELP: Check port permissions. Current user must be member of "dialout" group.')
    logging.info('Check port permissions. Current user must be member of "dialout" group.')
    sys.exit(1)
else:
    logging.info('LoStik port opened')
    Path('lostik.lock').touch()
    
#check LoStik firmware version
lostik.write(b'sys get ver\r\n')
if lostik.readline().decode('ASCII').rstrip() != 'RN2903 1.0.5 Nov 06 2018 10:45:27':
    print('ERROR: LoStik failed to return expected firmware version!')
    logging.error('LoStik failed to return expected firmware version!')
    sys.exit(1)

#attempt to pause mac (LoRaWAN) as required to issue commands directly to the radio
lostik.write(b'mac pause\r\n')
if lostik.readline().decode('ASCII').rstrip() != '4294967245':
    print('ERROR: Unable to pause LoRaWAN!')
    logging.error('Unable to pause LoRaWAN!')
    sys.exit(1)

#function: control lostik LEDs
def lostik_led_control(led, state): #values are rx/tx and on/off
    if led == 'rx':
        if state == 'off':
            lostik.write(b'sys set pindig GPIO10 0\r\n') #GPIO10 = blue rx led
            if lostik.readline().decode('ASCII').rstrip() == 'ok':
                return True
            else:
                return False
        elif state == 'on':
            lostik.write(b'sys set pindig GPIO10 1\r\n') #GPIO10 = blue rx led
            if lostik.readline().decode('ASCII').rstrip() == 'ok':
                return True
            else:
                return False
    elif led == 'tx':
        if state == 'off':
            lostik.write(b'sys set pindig GPIO11 0\r\n') #GPIO11 = red tx led
            if lostik.readline().decode('ASCII').rstrip() == 'ok':
                return True
            else:
                return False
        elif state == 'on':
            lostik.write(b'sys set pindig GPIO11 1\r\n') #GPIO11 = red tx led
            if lostik.readline().decode('ASCII').rstrip() == 'ok':
                return True
            else:
                return False
    else:
        return False

#initialize lostik for PiERS operation
#turn on both LEDs to indicate we are entering "initialization" mode
lostik_led_control('rx', 'on')
lostik_led_control('tx', 'on')

#write "network" settings to LoStik
#set frequency
lostik.write(b''.join([b'radio set freq ', set_freq, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('ERROR: Failed to set LoStik frequency to ' + set_freq.decode('UTF-8') + '!')
    logging.error('Failed to set LoStik frequency to ' + set_freq.decode('UTF-8') + '!')
    sys.exit(1)
#set mode
lostik.write(b''.join([b'radio set mod ', set_mod, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('ERROR: Failed to set LoStik modulation mode to LoRa!')
    logging.error('Failed to set LoStik modulation mode to LoRa!')
    sys.exit(1)
#set CRC header usage
lostik.write(b''.join([b'radio set crc ', set_crc, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('ERROR: Failed to enable LoStik CRC header setting!')
    logging.error('Failed to enable LoStik CRC header setting!')
    sys.exit(1)
#set IQ inversion
lostik.write(b''.join([b'radio set iqi ', set_iqi, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('ERROR: Failed to disable LoStik IQ inversion setting!')
    logging.error('Failed to disable LoStik IQ inversion setting!')
    sys.exit(1)
#set sync word
lostik.write(b''.join([b'radio set sync ', set_sync, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('ERROR: Failed to set LoStik sync word to ' + set_sync.decode('UTF-8') + '!')
    logging.error('Failed to set LoStik sync word to ' + set_sync.decode('UTF-8') + '!')
    sys.exit(1)
#set spreading factor
lostik.write(b''.join([b'radio set sf ', set_sf, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('ERROR: Failed to set LoStik spreading factor to ' + set_sf.decode('UTF-8') + '!')
    logging.error('Failed to set LoStik spreading factor to ' + set_sf.decode('UTF-8') + '!')
    sys.exit(1)
#set radio bandwidth
lostik.write(b''.join([b'radio set bw ', set_bw, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('ERROR: Failed to set LoStik radio bandwidth to ' + set_bw.decode('UTF-8') + '!')
    logging.error('Failed to set LoStik radio bandwidth to ' + set_bw.decode('UTF-8') + '!')
    sys.exit(1)
    
#write "node" settings to LoStik
#set power
lostik.write(b''.join([b'radio set pwr ', set_pwr, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('ERROR: Failed to set LoStik transmit power to ' + set_pwr.decode('UTF-8') + '!')
    logging.error('Failed to set LoStik transmit power to ' + set_pwr.decode('UTF-8') + '!')
    sys.exit(1)
#set coding rate
lostik.write(b''.join([b'radio set cr ', set_cr, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('ERROR: Failed to set LoStik coding rate to ' + set_cr.decode('UTF-8') + '!')
    logging.error('Failed to set LoStik coding rate to ' + set_cr.decode('UTF-8') + '!')
    sys.exit(1)
#set watchdog timer time-out
lostik.write(b''.join([b'radio set wdt ', set_wdt, b'\r\n']))
if lostik.readline().decode('ASCII').rstrip() != 'ok':
    print('ERROR: Failed to set LoStik watchdog timer time-out to ' + set_wdt.decode('UTF-8') + '!')
    logging.error('Failed to set LoStik watchdog timer time-out to ' + set_wdt.decode('UTF-8') + '!')
    sys.exit(1)

#turn off both LEDs to indicate we have exited "initialization" mode
lostik_led_control('rx', 'off')
lostik_led_control('tx', 'off')

logging.info('LoStik initialization complete')

#function: control lostik receive state
def lostik_rx_control(state): #state values are 'on' or 'off'
    if state == 'on':
        #place LoStik in continuous receive mode
        lostik.write(b'radio rx 0\r\n')
        if lostik.readline().decode('ASCII').rstrip() == 'ok':
            if lostik_led_control('rx', 'on'):
                return True
            else:
                return False
        else:
            return False
    elif state == 'off':
        #halt LoStik continuous receive mode
        lostik.write(b'radio rxstop\r\n')
        if lostik.readline().decode('ASCII').rstrip() == 'ok':
            if lostik_led_control('rx', 'off'):
                return True
            else:
                return False
        else:
            return False

#function: obtain rssi of last received packet
def lostik_get_rssi():
    lostik.write(b'radio get rssi\r\n')
    rssi = lostik.readline().decode('ASCII').rstrip()
    return rssi

#function: obtain snr of last received packet
def lostik_get_snr():
    lostik.write(b'radio get snr\r\n')
    snr = lostik.readline().decode('ASCII').rstrip()
    return snr

#function: tx cycle, accepts hex payload, attempts to transmit and returns boolean
def lostik_tx_cycle(payload_hex):
    if lostik_rx_control('off'):
        tx_command_elements = 'radio tx' + payload_hex + '\r\n'
        tx_command = tx_command_elements.encode('ASCII')
        lostik.write(tx_command)
        if lostik.readline().decode('ASCII').rstrip() == 'ok':
            lostik_led_control('tx', 'on')
        else:
            print('ERROR: Transmit failure!')
            logging.error('Transmit failure!')
            sys.exit(1)
        response = ''
        while response == '':
            response = lostik.readline().decode('ASCII').rstrip()
        else:
            if response == 'radio_tx_ok':
                lostik_led_control('tx', 'off')
                return True
            elif response == 'radio_err':
                lostik_led_control('tx', 'off')
                print('WARNING: Transmit failure! Radio error!')
                logging.warning('Transmit failure! Radio error!')
                return False
    else:
        print('WARNING: Transmit failure! Unable to halt LoStik continuous receive mode.')
        logging.warning('Transmit failure! Unable to halt LoStik continuous receive mode.')
        return False

#function: get next tx payload from piers.sqlite3




##### THIS IS WHERE I AM CURRENTLY WORKING #####




#function: cleanup
def at_exit():
    lostik_rx_control('off')
    lostik_led_control('rx', 'off')
    lostik_led_control('tx', 'off')
    lostik.close()
    if Path('lostik.lock').is_file():
        os.remove('lostik.lock')
    logging.info('LoStik port closed')
    logging.info('lostik.py %s stopped', version)
    logging.info('-------------------------------------------------------------------------------')

atexit.register(at_exit)






































# #function: bypass the print() buffer so we can write to the console direct
# def incremental_print(text):
#     sys.stdout.write(str(text))
#     sys.stdout.flush()

# #function: add received packet to database
# def database_rx(data_hex):
#     #convert from hex to plain text
#     data_raw = bytes.fromhex(data_hex).decode('ASCII')
#     #split on each instance of comma
#     data_raw = data_raw.split(',')
#     if int(data_raw[0]) == 1:







# #the listen loop

# while True:
#     if lostik_rx_control('on'):
#         incremental_print('Listening')
#         rx_data = ''
#         while rx_data == '':
#             rx_data = lostik.readline().decode('ASCII').rstrip()
#             incremental_print('.')
#         else:
#             if rx_data == 'radio_err':
#                 print('\n' + 'Radio Watchdog Timer Timeout' + '\n')
#                 if args.ping:
#                     ping()
#             else:
#                 rx_data_array = rx_data.split()
#                 if rx_data_array[0] == 'radio_rx':
#                     rssi = lostik_get_rssi()
#                     snr = lostik_get_snr()
#                     if args.pong:
#                         if bytes.fromhex(rx_data_array[1]).decode('ASCII') == 'Ping!':
#                             print('\n')
#                             print('Ping! Pong! (Heard a ping, now sending a pong!)')
#                             pong(rssi, snr)
#                     else:
#                         print('\n')
#                         print('    MSG: ' + bytes.fromhex(rx_data_array[1]).decode('ASCII'))
#                         print('   RSSI: ' + rssi + 'dBm')
#                         print('    SNR: ' + snr + 'dB\n')
#     else:
#         lostik_rx_control('off')










# #pong function
# def pong(send_rssi, send_snr):
#     if lostik_rx_control('off'):
#         tx_start_time = 0
#         tx_end_time = 0
#         send_rssi_bytes = send_rssi.encode('ASCII')
#         send_snr_bytes = send_snr.encode('ASCII')
#         send_msg_bytes = b''.join([b'Pong!  RSSI: ', send_rssi_bytes, b'dBm  SNR: ', send_snr_bytes, b'dB'])
#         send_msg_hex = send_msg_bytes.hex()
#         assemble_command = 'radio tx ' + send_msg_hex + '\r\n'
#         command = assemble_command.encode('ASCII')
#         print('PLAIN TEXT: radio tx ' + send_msg_bytes.decode('ASCII'))
#         print('  RAW DATA: ' + command.decode('ASCII').rstrip() + '\n')
#         lostik.write(command)
#         if lostik.readline().decode('ASCII').rstrip() == 'ok':
#             tx_start_time = int(round(time.time()*1000))
#             lostik_led_control('tx', 'on')
#             incremental_print('Transmitting')
#         else:
#             print('ERROR: Unable to transmit "Pong!" message.')
#             sys.exit(1)
#         response = ''
#         while response == '':
#             response = lostik.readline().decode('ASCII').rstrip()
#             incremental_print('.')
#         else:
#             if response == 'radio_tx_ok':
#                 tx_end_time = int(round(time.time()*1000))
#                 lostik_led_control('tx', 'off')
#                 tx_time = tx_end_time - tx_start_time
#                 incremental_print(' DONE!  Transmit time: ' + str(tx_time) + 'ms\n\n')
#             elif response == 'radio_err':
#                 lostik_led_control('tx', 'off')
#                 incremental_print(' FAILURE!\n')
# #the loop
# while True:
#     #if lostik successfully enters receive mode, do stuff
#     if lostik_rx_control('on'):
#         #start with a clear terminal window (refresh interface)
#         os.system('clear')
#         #print the interface to the console whilst incorporating the last
#         #known activity from the lostik
#         print('+------------------------------- LAST ACTIVITY -------------------------------+')
#         incremental_print('|                                                               ' + lostik_last_activity_ts + ' |\r')
#         incremental_print('| ' + lostik_last_activity + '\r')
#         print('+-----------------------------------------------------------------------------+')
#         print()
#         incremental_print('Listening.')    
#         #initialize rx_data variable
#         rx_data = None   
#         #while rx_data has no value, keep reading from lostik
#         #the while loop repeats based on serial read timeout (one second)
#         while rx_data == None:
#             #wait for byte array to be received over serial
#             rx_data = lostik.readline().decode('ASCII').rstrip()
#             #above line has 1 second timeout, then print . to show the user
#             #that the scipt is still running
#             incremental_print('.')   
#         #once we obtain something from lostik, process it
#         else:
#             #if lostik responds with radio_err, the most likely reason is the watchdog timer
#             if rx_data == 'radio_err':
#                 lostik_last_activity_ts = time.strftime(%H )
#                 lostik_last_activity = 'Radio Watchdog Timer Timeout'
#                 if args.ping:
#                     ping()
#             else:
#                 rx_data_array = rx_data.split()
#                 if rx_data_array[0] == 'radio_rx':
#                     rssi = lostik_get_rssi()
#                     snr = lostik_get_snr()
#                     if args.pong:
#                         if bytes.fromhex(rx_data_array[1]).decode('ASCII') == 'Ping!':
#                             print('\n')
#                             print('Ping! Pong! (Heard a ping, now sending a pong!)')
#                             pong(rssi, snr)
#                     else:
#                         print('\n')
#                         print('    MSG: ' + bytes.fromhex(rx_data_array[1]).decode('ASCII'))
#                         print('   RSSI: ' + rssi + 'dBm')
#                         print('    SNR: ' + snr + 'dB\n')
#     #if lostik fails to enter receive mode, exit receive mode and loop
#     else:
#         lostik_rx_control('off')