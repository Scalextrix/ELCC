#!/usr/bin/env python

"""sunviewer.py: Draws a basic chart based on sunfinder.py"""


__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.0"


import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import sqlite3

xaxischooser = raw_input('Plot energy against "date" or "blocks"? ')

conn = sqlite3.connect('solardetails.db')
c = conn.cursor()
energyplot = c.execute('select totalmwh FROM SOLARDETAILS').fetchall()
blocknumber = c.execute('select block FROM SOLARDETAILS').fetchall()
datetime = c.execute('select period FROM SOLARDETAILS').fetchall()
conn.close()

if xaxischooser == 'date':
	dates = [a[0][a[0].rfind(';')+1:] for a in datetime]
	date = [dt.datetime.strptime(d,'%Y-%m-%d %H:%M:%S') for d in dates]
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
	plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
	plt.plot(date, energyplot)
	plt.subplots_adjust(bottom=.4)
	plt.ylabel('Total Energy MWh')
	plt.xlabel('Time')
elif xaxischooser == 'blocks':
	plt.plot(blocknumber, energyplot)
	plt.ylabel('Total Energy MWh')
	plt.xlabel('SolarCoin Blocks')
else:
	print 'You must either choose "date" or "blocks"'

plt.xticks(rotation='vertical')
plt.show()

