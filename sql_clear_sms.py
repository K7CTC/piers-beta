########################################################################
#                                                                      #
#          NAME:  PiERS - Clear SMS Table                              #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                #
#       VERSION:  v1.0                                                 #
#   DESCRIPTION:  This script simply drops and recreates the sms       #
#                 table from piers.db thus purging all chat history.   #
#                                                                      #
########################################################################

import sqlite3
import sys
from pathlib import Path

if Path('piers.db').is_file():
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
                FOREIGN KEY (location_id) REFERENCES locations (location_id));''')
        db.commit()
        db.close()
    except:
        print('FAIL!')
        sys.exit(1)
    else:
        print('PASS!')
        sys.exit(0)
else:
    print('ERROR: File not found - piers.db')
    sys.exit(1)