########################################################################
#                                                                      #
#          NAME:  PiERS - Create PiERS SQLite 3 Database               #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                #
#       VERSION:  v1.0                                                 #
#   DESCRIPTION:  This script creates piers.db and populates it with   #
#                 event data from participants.csv and locations.csv   #
#                                                                      #
########################################################################

#import required modules
import sys
import sqlite3
import csv
from pathlib import Path

if Path('piers.db').is_file():
    print('ERROR: piers.db already exists')
    sys.exit(1)

if Path('participants.csv').is_file() == False:
    print('ERROR: File not found - participants.csv')
    sys.exit(1)

if Path('locations.csv').is_file() == False:
    print('ERROR: File not found - locations.csv')
    sys.exit(1)

try:
    db = sqlite3.connect('piers.db')
    db.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            participant_id                  INTEGER NOT NULL UNIQUE,
            participant_first_name	        TEXT,
            participant_last_name	        TEXT,
            participant_gender	            TEXT,
            participant_age	                INTEGER,
            participant_city	            TEXT,
            participant_state	            TEXT,
            participant_emergency_name	    TEXT,
            participant_emergency_phone	    TEXT,
            PRIMARY KEY (participant_id)
        );
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS locations (
            location_id	                    INTEGER NOT NULL UNIQUE,
            location_name	                TEXT NOT NULL,
            PRIMARY KEY(location_id)
        );
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS sms (
            location_id                     INTEGER NOT NULL,
            message	                        TEXT NOT NULL,
            payload_raw                     TEXT NOT NULL,
            payload_hex                     TEXT NOT NULL,
            time_queued	                    INTEGER,
            time_on_air	                    INTEGER,
            time_sent	                    INTEGER,
            tx_count                        INTEGER,
            time_received	                INTEGER,
            rssi                            INTEGER,
            snr                             INTEGER,
            duplicate	                    INTEGER,
            FOREIGN KEY (location_id) REFERENCES stations (location_id)
        );
    ''')
    db.commit()
    with open('participants.csv') as csvfile:
        participants = csv.DictReader(csvfile)
        to_db = [(i['participant_id'],
                  i['participant_first_name'],
                  i['participant_last_name'],
                  i['participant_gender'],
                  i['participant_age'],
                  i['participant_city'],
                  i['participant_state'],
                  i['participant_emergency_name'],
                  i['participant_emergency_phone'])
                  for i in participants]
    db.executemany('''
        INSERT INTO participants (
            participant_id,
            participant_first_name,
            participant_last_name,
            participant_gender,
            participant_age,
            participant_city,
            participant_state,
            participant_emergency_name,
            participant_emergency_phone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    ''', to_db)
    db.commit()
    with open('locations.csv') as csvfile:
        locations = csv.DictReader(csvfile)
        to_db = [(i['location_id'],
                  i['location_name'])
                 for i in locations]
    db.executemany('''
        INSERT INTO locations (
            location_id,
            location_name)
        VALUES (?, ?);
    ''', to_db)
    db.commit()
    db.close()
except:
    print('FAIL!')
    sys.exit(1)
else:
    print('PASS!')
    sys.exit(0)