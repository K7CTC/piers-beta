########################################################################
#                                                                      #
#          NAME:  PiERS - View SMS                                     #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                #
#       VERSION:  v1.0                                                 #
#   DESCRIPTION:  This module reads the sms table from piers.db once   #
#                 per second and displays the output to the console.   #
#                                                                      #
########################################################################

import datetime
import sqlite3
import sys
import time
from pathlib import Path

my_location_id = None

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

rowid_marker = 0

conn = sqlite3.connect('piers.db')
c = conn.cursor()
while True:
    try:    
        #get all rows with rowid greater than rowid_marker
        c.execute('''
            SELECT
                location_id,
                location_name,
                message,
                time_queued,
                time_received,
                rssi,
                snr,
                duplicate
            FROM
                locations
            NATURAL JOIN
                sms
            WHERE
                sms.rowid>? AND (duplicate='N' OR duplicate IS NULL)''',
                (rowid_marker,))
        for row in c.fetchall():
            print()
            if row[0] == location_id:
                unix_ts = int(row[3]) / 1000
                friendly_ts = datetime.datetime.fromtimestamp(unix_ts).strftime('%I:%M:%S %p')
                sms_length = len(row[2])
                if sms_length <= 11:
                    right_align_whitespace = ' ' * 53
                    sms_padding = ' ' * (11 - sms_length)
                    print(f'{right_align_whitespace}┌─────────────┐')
                    print(f'{right_align_whitespace}│ {sms_padding}{row[2]} │')
                    print(f'{right_align_whitespace}└┤{friendly_ts}├┘')
                else:
                    right_align_length = 64 - sms_length
                    right_align_whitespace = ' ' * right_align_length
                    border_top = '─' * sms_length
                    border_bottom = '─' * (sms_length - 12)
                    print(f'{right_align_whitespace}┌─{border_top}─┐')
                    print(f'{right_align_whitespace}│ {row[2]} │')
                    print(f'{right_align_whitespace}└─{border_bottom}┤{friendly_ts}├┘')
            else:
                unix_ts = int(row[4]) / 1000
                friendly_ts = datetime.datetime.fromtimestamp(unix_ts).strftime('%I:%M:%S %p')
                sms_length = len(row[2])
                if sms_length <= 11:
                    sms_padding = ' ' * (11 - sms_length)
                    print(f'┌─────────────┐')
                    print(f'│ {row[2]}{sms_padding} │')
                    print(f'└┤{friendly_ts}├┘')
                else:
                    border_top = '─' * sms_length
                    border_bottom = '─' * (sms_length - 12)
                    print(f'┌─{border_top}─┐')
                    print(f'│ {row[2]} │')
                    print(f'└┤{friendly_ts}├{border_bottom}─┘')
                    print(f'{(row[1])} (RSSI:{str(row[5])} SNR:{str(row[6])})')
        #now we need to update the rowid_maker to reflect what we have
        #already printed to the console
        c.execute('SELECT MAX(rowid) FROM sms')
        query_result = c.fetchone()
        if query_result:
            rowid_marker = query_result[0]
        time.sleep(1)
    except KeyboardInterrupt:
        print()
        break
c.close()
conn.close()
sys.exit(0)
