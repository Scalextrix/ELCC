#!/usr/bin/env python

"""sunviewer.py: Draws a basic chart based on sunfinder.py"""


__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "2.0"

import datetime as dt
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mpl_toolkits.basemap import Basemap
import numpy as np
import time
from Tkinter import PhotoImage
import sqlite3
import sys

def longitudeconverter(longitudes):
        if longitudes[-1] == 'W':
                longitudes = float('-'+longitudes[0:-1])
        else:
                longitudes = float(longitudes[0:-1])
        return longitudes

def latitudeconverter(latitudes):
        if latitudes[-1] == 'S':
                latitudes = float('-'+latitudes[0:-1])
        else:
                latitudes = float(latitudes[0:-1])
        return latitudes

userselector = raw_input('Enter a UserID or blank for all users ')
xaxischooser = raw_input('Plot energy against "date" or "blocks"? ')

conn = sqlite3.connect('solardetails.db')
c = conn.cursor()
if userselector == '':
	energyplot = [float(f[0]) for f in (c.execute('select totalmwh FROM GENDETAILS').fetchall())]
	incenergyplot = c.execute('select incrementmwh FROM GENDETAILS').fetchall()
	blocknumber = c.execute('select block FROM GENDETAILS').fetchall()
	datetime = c.execute('select period FROM GENDETAILS').fetchall()
        longitudes = c.execute('select lon FROM SYSDETAILS GROUP BY dataloggerid').fetchall()
        latitudes = c.execute('select lat FROM SYSDETAILS GROUP BY dataloggerid').fetchall()
        datalogger_id = c.execute('select DISTINCT dataloggerid FROM GENDETAILS').fetchall()
        conn.close()
        energysysname='Energy data from ElectriCChain for All Systems'
        mapsysname='Locations of All Systems'
else:
	energyplot = c.execute('select totalmwh FROM GENDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	incenergyplot = c.execute('select incrementmwh FROM GENDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	blocknumber = c.execute('select block FROM GENDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
	datetime = c.execute('select period FROM GENDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
        longitudes = c.execute('select DISTINCT lon FROM SYSDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
        latitudes = c.execute('select DISTINCT lat FROM SYSDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
        datalogger_id = c.execute('select DISTINCT dataloggerid FROM GENDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
        sysinfo = c.execute('select panelid, tilt, azimuth, inverterid, pkwatt, lat, lon, msg, datalogger FROM SYSDETAILS where dataloggerid="{}"'.format(userselector)).fetchall()
        conn.close()
        energysysname=('Energy data from ElectriCChain for System ID {}').format(userselector)
        mapsysname=('System Location for {}').format(userselector)

incenergyplot = [float(f[0]) for f in incenergyplot]
blocknumber = [int(f[0]) for f in blocknumber]
datalogger_id = [str(f[0]) for f in datalogger_id]
longitudes = [longitudeconverter(f[0]) for f in longitudes]
latitudes = [latitudeconverter(f[0]) for f in latitudes]
dates = [f[0] for f in datetime]

if xaxischooser == 'date':
	date = [dt.datetime.strptime(d,'%Y-%m-%d %H:%M:%S') for d in dates]
	plt.figure(num=1, figsize=(16, 12))
	thismanager = plt.get_current_fig_manager()
        img = PhotoImage(file='elcc_logo.ppm')
        thismanager.window.tk.call('wm', 'iconphoto', thismanager.window._w, img)
        plt.subplot(121)
        plt.title(energysysname)
	plt.gcf().canvas.set_window_title('ElectriCChain SunViewer v1.0')
	plt.subplots_adjust(left=0.06, bottom=0.13, right=0.9, top=0.9)
	plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M:%S'))
	plt.gca().xaxis.set_major_locator(mdates.AutoDateLocator())
	plt.plot(date, energyplot, 'bo')
	plt.ylabel('TOTAL Energy MWh', color='b')
	plt.tick_params('y', colors='b')
	plt.xlabel('Date & Time (UTC)')
	plt.xticks(rotation=45)
	plt.twinx()
	plt.bar(date, incenergyplot, width=0.01, align='center', color='r')
	plt.ylabel('INCREMENT Energy MWh', color='r')
	plt.tick_params('y', colors='r')

elif xaxischooser == 'blocks':
	plt.figure(num=1, figsize=(16, 12))
	thismanager = plt.get_current_fig_manager()
        img = PhotoImage(file='elcc_logo.ppm')
        thismanager.window.tk.call('wm', 'iconphoto', thismanager.window._w, img)
        plt.subplot(121)
        plt.title(energysysname)
	plt.gcf().canvas.set_window_title('ElectriCChain SunViewer v1.0')
	plt.subplots_adjust(left=0.06, bottom=0.13, right=0.98, top=0.9)
	plt.plot(blocknumber, energyplot, 'bo')
	plt.ylabel('TOTAL Energy MWh', color='b')
	plt.tick_params('y', colors='b')
	plt.xlabel('SolarCoin Blocks')
	plt.xticks(rotation=45)
	plt.twinx()
	plt.bar(blocknumber, incenergyplot, width=10.0, align='center', color='r')
	plt.ylabel('INCREMENT Energy MWh', color='r')
	plt.tick_params('y', colors='r')
else:
	print 'You must either choose "date" or "blocks", exit in 10 seconds'
	time.sleep(10)
	sys.exit()

if userselector == '':
        plt.subplot(122)
        plt.title(mapsysname)
        earth = Basemap(projection='mill')
        earth.drawcoastlines(color='0.50', linewidth=0.25)
        earth.fillcontinents(color='0.95', zorder=0)
        x, y = earth(longitudes, latitudes)
        earth.scatter(x, y, color='g', marker='o', linewidths=0.5)
        for i, txt in enumerate(datalogger_id):
                plt.annotate(txt, xy=(x[i], y[i]), xycoords='data', xytext=(8, -4), textcoords='offset points', wrap=True)
else:
        plt.subplot(122)
        plt.title(mapsysname)
        earth = Basemap(projection='mill')
        earth.drawcoastlines(color='0.50', linewidth=0.25)
        earth.fillcontinents(color='0.95', zorder=0)
        x, y = earth(longitudes, latitudes)
        earth.scatter(x, y, color='g', marker='o', linewidths=0.5)
        for i, txt in enumerate(sysinfo):
                plt.annotate(txt, xy=(x[i], y[i]), xycoords='data', xytext=(8, -4), textcoords='offset points', wrap=True)
plt.show()

