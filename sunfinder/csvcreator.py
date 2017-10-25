#!/usr/bin/env python

"""csvcreator.py: Converts the solardetails.db file, to .csv"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.0"

import sqlite3
import csv

conn = sqlite3.connect('solardetails.db')
c = conn.cursor()
export_system_data = c.execute('select * from SYSDETAILS').fetchall()
export_generation_data = c.execute('select * from GENDETAILS').fetchall()
conn.close()

with open('systemdetails.csv', 'wb') as f:
	writer = csv.writer(f)
	writer.writerow(['UserID', 'Solar_Panel', 'Inverter', 'PeakWatt', 'Deg_Tilt', 'Deg_Azimuth', 'Latitude', 'Longitude', 'Comment', 'Data-logger', 'SLR_Signature_Address'])
	writer.writerows(export_system_data)
	f.close()

with open('generationdetails.csv', 'wb') as f:
	writer = csv.writer(f)
	writer.writerow(['Generation_Unix_Time', 'UserID', 'Transaction_Hash', 'Block_Number', 'Unix_Block_Time', 'Generation_Date_Time', 'Total_MWh', 'Incremental_MWh'])
	writer.writerows(export_generation_data)
	f.close()	
