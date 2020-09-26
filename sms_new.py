########################################################################
#                                                                      #
#          NAME:  PiERS - New SMS                                      #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                #
#       VERSION:  v1.0                                                 #
#   DESCRIPTION:  This module reads piers.conf to obtain the location  #
#                 identifier and validates a user provided message of  #
#                 up to 50 characters.  An SMS packet type identifier  #
#                 is appended and the resulting data is inserted into  #
#                 a new row within the sms table of piers.db.          #
#                                                                      #
########################################################################

import argparse
import os
import re
import sqlite3
import sys
import time
from pathlib import Path

my_location_id = None
my_location_name = None

#establish and parse command line arguments
parser = argparse.ArgumentParser(description='PiERS Module - New SMS',
                                 epilog='Created by K7CTC. This module reads piers.conf to obtain '
                                        'the location identifier and validates a user provided '
                                        'message of up to 50 characters. An SMS packet type '
                                        'identifier is appended and the resulting data is '
                                        'inserted into a new row within the sms table of '
                                        'piers.db.')
parser.add_argument('-m', '--message', nargs='?', default=None,
                    help='message of up to 50 characters in length to be queued for transmission')
args = parser.parse_args()

if Path('piers.db').is_file() == False:
    print('ERROR: File not found - piers.db')
    sys.exit(1)

if Path('piers.conf').is_file() == False:
    print('ERROR: File not found - piers.conf')
    sys.exit(1)

#attempt to read and validate the location id integer from piers.conf
try:
    file = open('piers.conf')
    my_location_id = int(file.readline())
    file.close()
except:
    print('ERROR: Failed to read location id from piers.conf!')
    sys.exit(1)
if my_location_id < 1 or my_location_id > 99:
    print('ERROR: Location identifier out of range!')
    sys.exit(1)

#use location id to obtain corresponding location name from the database
try:
    db = sqlite3.connect('piers.db')
    c = db.cursor()
    c.execute('SELECT location_name FROM locations WHERE location_id=?',(my_location_id,))
    query_result = c.fetchone()
    if query_result:
        my_location_name = query_result[0]
    else:
        print('ERROR: Invalid location identifier!')
        c.close()
        db.close()
        sys.exit(1)
except:
    print('ERROR: Unable to connect to piers.db') 
    c.close()
    db.close()
    sys.exit(1)

#function: message validation
def validate_message(message_to_be_validated):
    #only contain A-Z a-z 0-9 . ? ! and between 1 and 50 chars in length
    if re.fullmatch('^[a-zA-Z0-9!?. ]{1,50}$', message_to_be_validated):
        return True
    else:
        return False

#function: insert message into database      
def database_entry(message):
    #compose raw packet to be sent over the air
    payload_raw = str(1) + ',' + str(my_location_id) + ',' + message
    #compose hex encoded version of raw packet to be sent over the air
    payload_hex = payload_raw.encode('UTF-8').hex()
    #attempt database entry
    try:
        db = sqlite3.connect('piers.db')
        c = db.cursor()
        #enable foreign key constraints
        c.execute('PRAGMA foreign_keys = ON')
        time_queued = int(round(time.time()*1000))
        c.execute('''
            INSERT INTO sms (
                location_id,
                message,
                payload_raw,
                payload_hex,
                time_queued,
                tx_count)
            VALUES (?, ?, ?, ?, ?, ?);''',
            (my_location_id, message, payload_raw, payload_hex, time_queued, 0))
    except:
        c.close()
        db.close()
        return False
    else:
        db.commit()
        c.close()
        db.close()
        return True

#if message provided via command line validate then insert into database
if args.message != None:
    if validate_message(args.message):
        #message is valid, insert into database then quit
        if database_entry(args.message):
            print('SUCCESS: Message has been queued for transmission.')
            sys.exit(0)
        else:
            print('ERROR: Database entry failure!')
            sys.exit(1)
    else:
        print('ERROR: Your message contained invalid characters or is of invalid length!')
        sys.exit(1)

#new sms loop
if args.message == None:
    while True:
        try:
            os.system('clear')
            print('┌────────┤PiERS Experimental LoRa Mesh Messenger - New SMS├────────┐')
            print('│ Type a message between 1 and 50 characters then press enter.     │')
            print('│ Your message may only contain A-Z a-Z 0-9 and the following      │')
            print('│ special characters: period, question mark and exclamation mark   │')
            print('└──────────────────────────────────────────────────────────────────┘')
            message = input(my_location_name + ': ')
            if validate_message(message):
                if database_entry(message):
                    print()
                    print('SUCCESS: Message has been queued for transmission.')
                    time.sleep(5)
            else:
                print()
                print('ERROR: Your message contained invalid characters or is of invalid length!')
                time.sleep(5)
        except KeyboardInterrupt:
            print()
            sys.exit(0)