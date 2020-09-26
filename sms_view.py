
########################################################################
#                                                                      #
#          NAME:  PiERS Module - View SMS                              #
#  DEVELOPED BY:  Chris Clement (K7CTC)                                #
#       VERSION:  v1.1                                                 #
#      LOCATION:  /home/pi/sms_view.py                                 #
#   DESCRIPTION:  This module reads the sms table from piers.sqlite3   #
#                 and displays the output to the console.              #
#                                                                      #
########################################################################

#import required modules
import datetime
import sqlite3
import sys
import time
from pathlib import Path

station_id = None

#attempt to read the station id integer from piers.conf
if Path('piers.conf').is_file():
    piers_conf_station_id = None
    try:
        file = open('piers.conf')
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
    print('ERROR: File not found - piers.conf')
    sys.exit(1)

rowid_marker = 0

if Path('piers.sqlite3').is_file():
    conn = sqlite3.connect('piers.sqlite3')
    c = conn.cursor()
    while True:
        try:    
            #get all rows with rowid greater than rowid_marker
            c.execute('''
                SELECT
                    station_id,
                    station_name,
                    message,
                    time_queued,
                    time_received,
                    rssi,
                    snr,
                    duplicate
                FROM
                    stations
                NATURAL JOIN
                    sms
                WHERE
                    sms.rowid>? AND (duplicate='N' OR duplicate IS NULL)''',
                    (rowid_marker,))
            for row in c.fetchall():
                print()
                if row[0] == station_id:
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
else:
    print('ERROR: File not found - piers.sqlite3')
    sys.exit(1)