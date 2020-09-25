#!/usr/bin/env python3

########################################################################
#                                                                      #
#          NAME:  PiERS Module - Create New SMS                        #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                #
#       VERSION:  v1.1                                                 #
#      LOCATION:  /home/pi/sms_new.py                                  #
#   DESCRIPTION:  This module reads piers.conf to obtain the station   #
#                 identifier and validates a user provided message of  #
#                 up to 50 characters.  An SMS packet type identifier  #
#                 is appended and the resulting data is inserted into  #
#                 a new row within the sms table of the piers.sqlite3  #
#                 database.                                            #
#                                                                      #
########################################################################

#import required modules
import argparse
import os
import re
import sqlite3
import sys
import time

#module version
version = 'v1.1'

#file paths - mac (development)
path_database = '/home/pi/git/piers-chat-beta/piers.sqlite3'
path_piers_conf = '/home/pi/git/piers-chat-beta/piers.conf'

#file paths - pi (production)
#path_database = '/home/pi/piers.sqlite3'
#path_piers_conf = '/home/pi/piers.conf'

#establish and parse command line arguments
parser = argparse.ArgumentParser(description='PiERS Module - Create New SMS',
                                 epilog='Created by K7CTC. This module reads piers.conf to obtain '
                                        'the station identifier and validates a user provided '
                                        'message of up to 50 characters. An SMS packet type '
                                        'identifier is appended and the resulting data is '
                                        'inserted into a new row within the sms table of the '
                                        'piers.sqlite3 database.')
parser.add_argument('-m', '--message', nargs='?', default=None,
                    help='message of up to 50 characters in length to be queued for transmission')
args = parser.parse_args()

#attempt to read the station id integer from piers.conf
station_id = None
if os.path.isfile(path_piers_conf):
    piers_conf_station_id = None
    try:
        file = open(path_piers_conf)
        piers_conf_station_id = int(file.readline())
        file.close()
    except:
        print('ERROR: Unable to read station id from piers.conf!')
        sys.exit(1)
    if piers_conf_station_id >= 1 and piers_conf_station_id <= 99:
        station_id = piers_conf_station_id
    else:
        print('ERROR: Station identifier out of range!')
        sys.exit(1)
else:
    print('ERROR: File not found - ' + path_piers_conf)
    sys.exit(1)

#use station id to obtain corresponding station name from the database
station_name = None
if os.path.isfile(path_database):
    conn = sqlite3.connect(path_database)
    c = conn.cursor()
    c.execute('SELECT station_name FROM stations WHERE station_id=?',(station_id,))
    query_result = c.fetchone()
    if query_result:
        station_name = query_result[0]
    else:
        print('ERROR: Invalid station identifier!')
        c.close()
        conn.close()
        sys.exit(1)        
    c.close()
    conn.close()
else:
    print('ERROR: File not found - ' + path_database)
    sys.exit(1)

#function for message validation
def validate_message(message_to_be_validated):
    #only contain A-Z a-z 0-9 . ? ! and between 1 and 50 chars in length
    if re.fullmatch('^[a-zA-Z0-9!?. ]{1,50}$', message_to_be_validated):
        return True
    else:
        return False
        
def database_entry(message):
    #compose raw packet to be sent over the air
    payload_raw = str(1) + ',' + str(station_id) + ',' + message
    #compose hex encoded version of raw packet to be sent over the air
    payload_hex = payload_raw.encode('UTF-8').hex()
    #connect to database
    conn = sqlite3.connect(path_database)
    c = conn.cursor()
    #enable foreign key constraints
    c.execute('PRAGMA foreign_keys = ON')
    try:
        time_queued = int(round(time.time()*1000))
        c.execute('''
            INSERT INTO sms (
                station_id,
                message,
                payload_raw,
                payload_hex,
                time_queued,
                tx_count)
            VALUES (?, ?, ?, ?, ?, ?)''',
            (station_id, message, payload_raw, payload_hex, time_queued, 0))
    except sqlite3.IntegrityError:
        c.close()
        conn.close()
        return False
    except:
        c.close()
        conn.close()
        return False
    conn.commit()
    c.close()
    conn.close()
    return True

#if message provided via command line validate then insert into database
if args.message != None:
    if validate_message(args.message):
        #message is valid, insert into database then quit
        if database_entry(args.message):
            print('SUCCESS: Your message has been queued for transmission.')
            sys.exit(0)
        else:
            print('ERROR: An unknown error occurred!')
    else:
        print('ERROR: Your message contained invalid characters or its length was invalid!')
        sys.exit(1)

#function to bypass the print() buffer, write directly to the console
def incremental_print(text):
    sys.stdout.write(str(text))
    sys.stdout.flush()

#message loop
if args.message == None:
    countdown_message = [
        ' ',
        '        [1]   MESSAGE HAS BEEN QUEUED FOR TRANSMISSION   [1]        ',
        '      [2]     MESSAGE HAS BEEN QUEUED FOR TRANSMISSION     [2]      ',
        '    [3]       MESSAGE HAS BEEN QUEUED FOR TRANSMISSION       [3]    ',
        '  [4]         MESSAGE HAS BEEN QUEUED FOR TRANSMISSION         [4]  ',
        '[5]           MESSAGE HAS BEEN QUEUED FOR TRANSMISSION           [5]'
    ]
    countdown_number = [
        '   ',
        '[1]',
        '[2]',
        '[3]',
        '[4]',
        '[5]'
    ]
    while True:
        try:
            #start with a clear terminal window
            os.system('clear')
            print('┌───┤PiERS Experimental LoRa Mesh Messenger - Create New SMS├──────┐')
            print('│ Please type a message between 1 and 50 characters then press     │')
            print('│ enter.  Your message may only contain A-Z a-Z 0-9 and the        │')
            print('│ following special characters:                                    │')
            print('│ period, question mark and exclamation mark                       │')
            print('└──────────────────────────────────────────────────────────────────┘')
            message = input(station_name + ': ')
            if validate_message(message):
                if database_entry(message):
                    print()
                    countdown_seconds = 5
                    while countdown_seconds > 0:
                        incremental_print(countdown_message[countdown_seconds] + '\r')
                        time.sleep(1)
                        countdown_seconds = countdown_seconds - 1
            else:
                print()
                countdown_seconds = 5
                error_message = ('ERROR: Your message contained invalid characters or its length '
                                 'was invalid!')
                while countdown_seconds > 0:
                    incremental_print(error_message + countdown_number[countdown_seconds] + '\r')
                    time.sleep(1)
                    countdown_seconds = countdown_seconds -1
        except KeyboardInterrupt:
            print()
            sys.exit(0)