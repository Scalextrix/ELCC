#!/usr/bin/env python

"""sunviewer.py: Draws a basic chart based on sunfinder.py"""


__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.0"


import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import time
import sqlite3
import sys

userselector = raw_input('Enter a UserID or blank for all users ')
xaxischooser = raw_input('Plot energy against "date" or "blocks"? ')

conn = sqlite3.connect('solardetails.db')
c = conn.cursor()
if userselector == '':
	energyplot = c.execute('select totalmwh FROM SOLARDETAILS').fetchall()
	blocknumber = c.execute('select block FROM SOLARDETAILS').fetchall()
	datetime = c.execute('select period FROM SOLARDETAILS').fetchall()
	conn.close()
else:
	energyplot = c.execute('select totalmwh FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	incenergyplot = c.execute('select increment_mwh FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	blocknumber = c.execute('select block FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	datetime = c.execute('select period FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	conn.close()

energyplot = [float(f[0]) for f in energyplot]
incenergyplot = [float(f[0]) for f in incenergyplot]
blocknumber = [int(f[0]) for f in blocknumber]
datetime = [str(f[0]) for f in datetime]

if xaxischooser == 'date':
	plt.title('Data from ElectriCChain')
	dates = [a[0][a[0].rfind(';')+1:] for a in datetime]
	date = [dt.datetime.strptime(d,'%Y-%m-%d %H:%M:%S') for d in dates]
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
	plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
	plt.figure(1)
	plt.subplot(211)
	plt.plot(date, energyplot, 'go')
	plt.ylabel('TOTAL Energy MWh')
	plt.xlabel('Date & Time (UTC)')
	plt.xticks(rotation='vertical')
	plt.subplots_adjust(bottom=.4)
	plt.subplot(212)
	plt.plot(date, incenergyplot, 'ro')
	plt.ylabel('INCREMENTAL Energy MWh')
	plt.xticks(rotation='vertical')
	plt.subplots_adjust(bottom=.4)
	plt.show()
elif xaxischooser == 'blocks':
	plt.title('Data from ElectriCChain')
	plt.figure(1)
	plt.subplot(211)
	plt.plot(blocknumber, energyplot, 'go')
	plt.ylabel('TOTAL Energy MWh')
	plt.xlabel('SolarCoin Blocks')
	plt.subplots_adjust(bottom=.4)
	plt.subplot(212)
	plt.bar(blocknumber, incenergyplot, width=10.0, align='center', color='r')
	plt.ylabel('INCREMENTAL Energy MWh')
	plt.xlabel('SolarCoin Blocks')
	plt.subplots_adjust(bottom=.4)
	plt.show()
else:
	print 'You must either choose "date" or "blocks", exit in 10 seconds'
	time.sleep(10)
	sys.exit()
