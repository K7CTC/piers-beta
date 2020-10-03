# PiERS - ACME 5K

ACME 5K is the "control" event for PiERS.  The intent is to simulate a small scale 5K foot race.  Seeing is how it is only a 5K, we're only going to need a handful of stations:

1. Start Line
2. Aid 01
3. Finish Line
4. Data/Net Control

These four stations provide all that is necessary to test the functionality and features of the system.  This race will have a cap of 150 participants.  The provided database has complete details for 125 completely fictional participants who have "registered" for the event.  Of course, some will register at the last moment and others will simply not show up for the event.  These are just a couple scenarios that the software must account for.

## event.sqlite3

As you might have guessed, PiERS uses a SQLite v3 database to store all pertinent event data.  
