########################################################################
#                                                                      #
#          NAME:  PiERS - Clear SMS Table                              #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                #
#       VERSION:  v1.0                                                 #
#   DESCRIPTION:  This script simply drops and recreates the sms       #
#                 table from piers.db thus purging all chat history.   #
#                                                                      #
########################################################################

#import required modules
import sys
import sqlite3
from pathlib import Path

if Path('piers.sqlite3').is_file() == False:
    print('ERROR: File not found - piers.sqlite3')
    sys.exit(1)

try:
    db = sqlite3.connect('piers.db')
    db.execute('DROP TABLE IF EXISTS sms')
    db.commit()
    db.execute('''
        CREATE TABLE IF NOT EXISTS sms (
            location_id     INTEGER NOT NULL,
            message	        TEXT NOT NULL,
            payload_raw     TEXT NOT NULL,
            payload_hex     TEXT NOT NULL,
            time_queued	    INTEGER,
            time_on_air	    INTEGER,
            time_sent	    INTEGER,
            tx_count        INTEGER,
            time_received	INTEGER,
            rssi            INTEGER,
            snr             INTEGER,
            duplicate	    INTEGER,
            FOREIGN KEY (location_id) REFERENCES stations (location_id)
        );
    ''')
    db.commit()
    db.close()
except:
    print('FAIL!')
    sys.exit(1)
else:
    print('PASS!')
    sys.exit(0)