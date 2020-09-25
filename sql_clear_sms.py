########################################################################
#                                                                      #
#          NAME:  PiERS - Clear SMS                                    #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                #
#       VERSION:  v1.1                                                 #
#      LOCATION:  /home/pi/sql_clear_sms.py                            #
#   DESCRIPTION:  This script simply deletes and recreates the sms     #
#                 table from piers.sqlite3 thus purging all chat       #
#                 history.                                             #
#                                                                      #
########################################################################

#import required modules
import sys
import sqlite3
from pathlib import Path

if Path('piers.sqlite3').is_file() == False:
    print('ERROR: File not found - piers.sqlite3')
    sys.exit(1)

conn = sqlite3.connect('piers.sqlite3')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS sms')
conn.commit()
c.execute('''
    CREATE TABLE IF NOT EXISTS sms (
        station_id      INTEGER NOT NULL,
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
        FOREIGN KEY (station_id) REFERENCES stations (station_id)
    )
''')
conn.commit()
c.close()
conn.close()
print('DONE!')
sys.exit(0)