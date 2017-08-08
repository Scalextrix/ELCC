#!/usr/bin/env python

"""noderedtest.py: Queries the solar PV datalogger device on LAN or web, pulls production data and 
instructs the solarcoin daemon to make a transaction to record onto blockchain"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "2.0"

# import python libraries we need for the program to work
import gc
import getpass
import json
import mininmalmodbus
import os.path
import subprocess
import sqlite3
import sys
import time
from urllib2 import urlopen

# Sets the frequency with which the reports will be made to block-chain, value in MWh, 0.01 = 10kWh
energy_reporting_increment = 0.01
# Sets the frequency that the Node-Red database is queried, value in Seconds
inverter_query = 600
# Collects the users Solarcoin Wallet passphrase, we need this for later to lock/unlock the wallet
solarcoin_passphrase = getpass.getpass(prompt="What is your SolarCoin Wallet Passphrase: ")

# Check if the user ran the program already and if a database of their system details already exists
if os.path.isfile("API.db"):
	print("Found API database")
else:
        # Ask the user for some system information
        solarcoin_address = raw_input ("What is your SolarCoin Address: ")
        solar_panel = raw_input ("What is the Make, Model & Part Number of your solar panel: ")
        solar_inverter = raw_input ("What is the Make, Model & Part Number of your inverter: ")
        peak_watt = raw_input ("In kW (kilo-Watts), what is the peak output of your system: ")
        latitude = raw_input ("What is the Latitude of your installation: ")
        longitude = raw_input ("What is the Longitude of your installation: ")
        message = raw_input ("Add an optional message describing your system: ")
        rpi = raw_input ("If you are staking on a Raspberry Pi note the Model: ")
        # Create a database and commit the answers, save the user from re-entering every time the program is run
        conn = sqlite3.connect("API.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS SYSTEMDETAILS (SLRaddress TEXT, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT)''')
        c.execute("INSERT INTO SYSTEMDETAILS VALUES (?,?,?,?,?,?,?,?);", (solarcoin_address, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi,))
        conn.commit()		
        conn.close()
        
# Fetch the users details from the database
conn = sqlite3.connect("API.db")
c = conn.cursor()
solarcoin_address = c.execute('select SLRaddress from SYSTEMDETAILS').fetchall()
solar_panel = c.execute('select panelid from SYSTEMDETAILS').fetchall()
solar_inverter = c.execute('select inverterid from SYSTEMDETAILS').fetchall()
peak_watt = c.execute('select pkwatt from SYSTEMDETAILS').fetchall()
latitude = c.execute('select lat from SYSTEMDETAILS').fetchall()
longitude = c.execute('select lon from SYSTEMDETAILS').fetchall()
message = c.execute('select msg from SYSTEMDETAILS').fetchall()
rpi = c.execute('select pi from SYSTEMDETAILS').fetchall()
conn.close()
# Values from the database are in a tuple of tuples format, we need to convert them to plain strings to use them later
envoy_ip = str(envoy_ip[0][0])
solarcoin_address = str(solarcoin_address[0][0])
solar_panel = str(solar_panel[0][0])
solar_inverter = str(solar_inverter[0][0])
peak_watt = str(peak_watt[0][0])
latitude = str(latitude[0][0])
longitude = str(longitude[0][0])
message = str(message[0][0])
rpi = str(rpi[0][0])

# Start a LOOP to query the Node-Red database and post to block-chain, this is where we need to do some work
while True:
	print("Calling Node-Red")
	# If Node-Red is using an sqlite database as seen here https://www.npmjs.com/package/node-red-node-sqlite perhaps some code like this
	# conn = sqlite3.connect("NodeRed.db")
        # c = conn.cursor()
        # total_energy = c.execute('select Watthours from NodeRed').fetchall()
        # conn.close()

        # Or if Node-red outputs to a .csv file perhaps some code like this
        # filename = "home/pi/.node-red/nodered.csv"
        # filename.encode('utf-8')
                # with open(filename, 'rb') as NN:
                # reader = csv.DictReader(NN)
                # feilds = [(i['Time'], i['WattHours']) for i in reader]
		
	# Or we may just be able to pull the Watt-hours reading directly from the SunSpec inverter
	# instr = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
	# total_energy = instr.read_register(40094, 1)
                
        # Depending how the data is structured we may need to parse / convert the Watt-hours value to a floating point number
        # total_energy = float(?)
	print("Total Energy MWh: {:.6f}") .format(total_energy)

        # Create a new local database table to store the Watt-hour values from Node-Red, we might not need to depending on what we are able to do with the Node-Red database
	conn = sqlite3.connect("API.db")
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL)''')
	c.execute("INSERT INTO ENERGYLOG VALUES (NULL,?);", (total_energy,))
	conn.commit()		
	conn.close()
        # Extract the first Watt-hour value from the database, find the last row and extract the last Watt-hour value, each time this LOOP runs a new last row is added
	conn = sqlite3.connect("APIlan.db")
	c = conn.cursor()
	start_energy = c.execute('select totalenergy from ENERGYLOG').fetchone()
	row_count = c.execute('select max(id) FROM ENERGYLOG').fetchone()[0]
	end_energy = c.execute('select totalenergy from ENERGYLOG where id={}'.format(row_count)).fetchone()
	conn.close()
	# Convert the list type Watt-hour values extracted from the database to floating point numbers
	start_energy = str(start_energy)[1:-2]
	end_energy = str(end_energy)[1:-2]
	start_energy = float(start_energy)
	end_energy = float(end_energy)

	# Check if there has been at least 10kWh of energy produced
	if end_energy >= (start_energy + energy_reporting_increment):
		print("Initiating SolarCoin")
		# If we did create 10kWh of energy, concatenate a string conforming to the ELCC standard from all the elements of solar system info and Watt-hours produced
		energylifetime = str('Note this is all public information '+solar_panel+'; '+solar_inverter+'; '+peak_watt+'kW ;'+latitude+','+longitude+'; '+message+'; '+rpi+'; Total MWh: {}' .format(total_energy))
		print("SolarCoin TXID:")
		# Issue commands to the solarcoin wallet to: lock, unlock, send the transaction, lock and unlock for staking only
		subprocess.call(['solarcoind', 'walletlock'], shell=False)
		subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999'], shell=False)
		subprocess.call(['solarcoind', 'sendtoaddress', solarcoin_address, '0.000001', '', '', energylifetime], shell=False)
		subprocess.call(['solarcoind', 'walletlock'], shell=False)
		subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999', 'true'], shell=False)
		# Clean the Watt-hours values from the database, when the LOOP runs again it will start a new first row, and append new values each time the LOOP re runs
		conn= sqlite3.connect("API.db")
		c = conn.cursor()
		c.execute('''DROP TABLE IF EXISTS ENERGYLOG''')
		conn.commit()		
		conn.close()
		gc.collect()		
	else:
                # If 10kWh has not been produced, wait some time, then start the LOOP again
                print "Waiting %s seconds" % inverter_query
		time.sleep(inverter_query)

		
	


