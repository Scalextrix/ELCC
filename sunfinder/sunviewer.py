#!/usr/bin/env python

"""sunviewer.py: Draws a basic chart based on sunfinder.py"""


__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.0"


import datetime as dt
import matplotlib as mpl
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import time
import sqlite3
import sys

def latitudeconverter(latitudes):
	if latitudes[-1] == 'S':
		latitudes = float('-'+latitudes[0:-1])
	else:
		latitudes = float(latitudes[0:-1])
	return latitudes

def longitudeconverter(longitudes):
	if longitudes[-1] == 'W':
		longitudes = float('-'+longitudes[0:-1])
	else:
		longitudes = float(longitudes[0:-1])
	return longitudes

userselector = raw_input('Enter a UserID or blank for all users ')
xaxischooser = raw_input('Plot energy against "date" or "blocks"? ')

conn = sqlite3.connect('solardetails.db')
c = conn.cursor()
if userselector == '':
	energyplot = c.execute('select totalmwh FROM SOLARDETAILS').fetchall()
	incenergyplot = c.execute('select incrementmwh FROM SOLARDETAILS').fetchall()
	blocknumber = c.execute('select block FROM SOLARDETAILS').fetchall()
	datetime = c.execute('select period FROM SOLARDETAILS').fetchall()
	longitudes = c.execute('select lon FROM SOLARDETAILS GROUP BY dataloggerid').fetchall()
	latitudes = c.execute('select lat FROM SOLARDETAILS GROUP BY dataloggerid').fetchall()
	datalogger_id = c.execute('select DISTINCT dataloggerid FROM SOLARDETAILS').fetchall()
	conn.close()
	sysname='Energy data from ElectriCChain for All Systems'
else:
	energyplot = c.execute('select totalmwh FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	incenergyplot = c.execute('select incrementmwh FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	blocknumber = c.execute('select block FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	datetime = c.execute('select period FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	longitudes = c.execute('select DISTINCT lon FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	latitudes = c.execute('select DISTINCT lat FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	datalogger_id = c.execute('select DISTINCT dataloggerid FROM SOLARDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	conn.close()
	sysname=('Energy data from ElectriCChain for System ID {}').format(userselector)

energyplot = [float(f[0]) for f in energyplot]
incenergyplot = [float(f[0]) for f in incenergyplot]
blocknumber = [int(f[0]) for f in blocknumber]
longitudes = [longitudeconverter(f[0]) for f in longitudes]
latitudes = [latitudeconverter(f[0]) for f in latitudes]
datalogger_id = [str(f[0]) for f in datalogger_id]

if xaxischooser == 'date':
	dates = [a[0][a[0].rfind(';')+1:] for a in datetime]
	date = [dt.datetime.strptime(d,'%Y-%m-%d %H:%M:%S') for d in dates]
	plt.figure(num=1, figsize=(10, 8))
	plt.subplots_adjust(left=0.06, bottom=0.13, right=0.9, top=0.9)
	plt.title(sysname)
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
	plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
	plt.plot(date, energyplot, 'bo')
	plt.ylabel('TOTAL Energy MWh', color='b')
	plt.tick_params('y', colors='b')
	plt.xlabel('Date & Time (UTC)')
	plt.xticks(rotation=45)
	plt.twinx()
	plt.bar(date, incenergyplot, width=0.01, align='center', color='r')
	plt.ylabel('INCREMENTAL Energy MWh', color='r')
	plt.tick_params('y', colors='r')

elif xaxischooser == 'blocks':
	plt.figure(num=1, figsize=(10, 8))
	plt.subplots_adjust(left=0.06, bottom=0.13, right=0.98, top=0.9)
	plt.title(sysname)
	plt.plot(blocknumber, energyplot, 'bo')
	plt.ylabel('TOTAL Energy MWh', color='b')
	plt.tick_params('y', colors='b')
	plt.xlabel('SolarCoin Blocks')
	plt.xticks(rotation=45)
	plt.twinx()
	plt.bar(blocknumber, incenergyplot, width=10.0, align='center', color='r')
	plt.ylabel('INCREMENTAL Energy MWh', color='r')
	plt.tick_params('y', colors='r')
else:
	print 'You must either choose "date" or "blocks", exit in 10 seconds'
	time.sleep(10)
	sys.exit()

plt.figure(num=2, figsize=(8, 6))
earth = Basemap(projection='mill')
earth.drawcoastlines(color='0.50', linewidth=0.25)
earth.fillcontinents(color='0.95', zorder=0)
x, y = earth(longitudes, latitudes)
earth.scatter(x, y, color='g', marker='o', linewidths=0.25)
for i, txt in enumerate(datalogger_id):
	plt.annotate(txt, xy=(x[i], y[i]), xycoords='data', xytext=(4, -4), textcoords='offset points', clip_on=True)
plt.show()
