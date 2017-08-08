#!/usr/bin/env python

"""datalogger.py: Queries the solar PV datalogger device using a generation meter with LED pulse set to 1 pulse per 1 Wh, 
pulls production data and instructs the solarcoin daemon to make a transaction to record onto blockchain"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "4.0"

import gc
import getpass
import json
import os.path
import RPi.GPIO as gpio
import subprocess
import sqlite3
import sys
import time
import urllib2

energy_reporting_increment = 0.01 # Sets the frequency with which the reports will be made to block-chain, value in MWh e.g. 0.01 = 10kWh
inverter_query_increment = 0
manufacturer_attribution = ""
gpio.setmode(gpio.BCM)
gpio.setup(17, gpio.IN)
dbname = "LED.db"

def calculateamounttosend():
	wallet_balance = float(subprocess.check_output(['solarcoind', 'getbalance'], shell=False))
	if wallet_balance < 0.0005:
		print ("*******ERROR: wallet balance of {}SLR too low for reliable datalogging, add more SLR to wallet *******") .format(wallet_balance)
		time.sleep(10)
		sys.exit()
	elif wallet_balance >= 10:
		send_amount = str(1)
		print ('Based on wallet balance of {} amount to send to self set to {} SLR') .format(wallet_balance, send_amount)
	elif wallet_balance < 10 and wallet_balance >= 0.03:
		send_amount = str(0.01)
		print ('Based on wallet balance of {} amount to send to self set to {} SLR') .format(wallet_balance, send_amount)
	else:
		send_amount = str(0.00001)
		print ("*******WARNING: low wallet balance of {}SLR, send amount of {} may result in higher TX fees*******") .format(wallet_balance, send_amount)
	return send_amount

def currentenergycounter(channel):
	global current_energy
	current_energy = current_energy + 0.000001
	print "\033[K", "Current kWh {}".format (current_energy * 1000), "\r",
	sys.stdout.flush()

def databasecreate():
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS SYSTEMDETAILS (SLRaddress TEXT, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT)''')
	c.execute("INSERT INTO SYSTEMDETAILS VALUES (?,?,?,?,?,?,?,?);", (solarcoin_address, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi,))
	conn.commit()
	conn.close()

def databasenamebroken():
	del solarcoin_passphrase
	gc.collect()
	print "*******ERROR: Exiting in 10 seconds: Database name corrupted, delete *.db file and try again *******"
	time.sleep(10)
	sys.exit()

def latitudetest():
	while True:
		latitude = raw_input ("What is the Latitude of your installation: ").upper()
		if latitude[-1] == 'N' or latitude[-1] == 'S':
			try:
				lat_float = float(latitude[:-1])
				if lat_float <= 90:
					return latitude
				else:
					print "*******ERROR: Latitude cannot be larger than 90.000N or 90.000S *******"
			except ValueError:
				print "*******ERROR: You must enter Latitude in a form 3.456N or 4.567S *******"
		else:
			print "*******ERROR: You must enter Latitude in a form 3.456N or 4.567S *******"

def longitudetest():
	while True:
		longitude = raw_input ("What is the Longitude of your installation: ").upper()
		if longitude[-1] == 'E' or longitude[-1] == 'W':
			try:
				lon_float = float(longitude[:-1])
				if lon_float <= 180:
					return longitude
				else:
					print "*******ERROR: Longitude cannot be larger than 180.000E or 180.000W *******"
			except ValueError:
				print "*******ERROR: You must enter Longitude in a form 3.456E or 4.567W *******"
		else:
			print "*******ERROR: You must enter Longitude in a form 3.456E or 4.567W *******"

def maintainenergylog():
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL, time REAL)''')
	now_time = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
	c.execute("INSERT INTO ENERGYLOG VALUES (NULL,?,?);", (total_energy, now_time))
	conn.commit()
	row_count = c.execute('select max(id) FROM ENERGYLOG').fetchone()[0]
	start_energy = float(c.execute('select totalenergy from ENERGYLOG').fetchone()[0])
	start_time = str(c.execute('select time from ENERGYLOG').fetchone()[0])
	end_energy = float(c.execute('select totalenergy from ENERGYLOG where id={}'.format(row_count)).fetchone()[0])
	end_time = str(c.execute('select time from ENERGYLOG where id={}'.format(row_count)).fetchone()[0])
	conn.close()
	return{'start_energy':start_energy, 'start_time':start_time, 'end_energy':end_energy, 'end_time':end_time}

def passphrasetest():
	solarcoin_passphrase = getpass.getpass(prompt="What is your SolarCoin Wallet Passphrase: ")
	print "Testing SolarCoin Wallet Passphrase, locking wallet..."
	try:
		subprocess.call(['solarcoind', 'walletlock'], shell=False)
		subprocess.check_output(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999', 'true'], shell=False)
	except subprocess.CalledProcessError:
		print "*******ERROR: Exiting in 10 seconds, SOLARCOIN WALLET NOT STAKING *******"
		time.sleep(10)
		sys.exit()
	else:
		print "SolarCoin Wallet Passphrase correct, wallet unlocked for staking"
		return solarcoin_passphrase

def peakwatttest():
	while True:
		peak_watt = raw_input ("In kW (kilo-Watts), what is the peak output of your system: ")
		try:
			peak_watt = float(peak_watt)
			return peak_watt
		except ValueError:
			print "*******ERROR: You must enter numbers and decimal point only e.g. 3.975 *******"

def refreshenergylogandsleep():
	conn= sqlite3.connect(dbname)
	c = conn.cursor()
	row_count = c.execute('select max(id) FROM ENERGYLOG').fetchone()[0]
	now_time = str(c.execute('select time from ENERGYLOG where id={}'.format(row_count)).fetchone()[0])
	c.execute('''DROP TABLE IF EXISTS ENERGYLOG''')
	conn.commit()
	c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL, time REAL)''')
	c.execute("INSERT INTO ENERGYLOG VALUES (NULL,?,?);", (total_energy, now_time))
	conn.commit()
	conn.close()
	print ("Waiting {:.0f} seconds (approx {:.2f} days)") .format(inverter_query_increment, (inverter_query_increment/86400))
	print ("******** "+manufacturer_attribution+" ********")
	time.sleep(inverter_query_increment)

def retrievecommoncredentials():
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	solarcoin_address = str(c.execute('select SLRaddress from SYSTEMDETAILS').fetchone()[0])
	solar_panel = str(c.execute('select panelid from SYSTEMDETAILS').fetchone()[0])
	solar_inverter = str(c.execute('select inverterid from SYSTEMDETAILS').fetchone()[0])
	peak_watt = str(c.execute('select pkwatt from SYSTEMDETAILS').fetchone()[0])
	latitude = str(c.execute('select lat from SYSTEMDETAILS').fetchone()[0])
	longitude = str(c.execute('select lon from SYSTEMDETAILS').fetchone()[0])
	message = str(c.execute('select msg from SYSTEMDETAILS').fetchone()[0])
	rpi = str(c.execute('select pi from SYSTEMDETAILS').fetchone()[0])
	conn.close()
	return {'solarcoin_address':solarcoin_address, 'solar_panel':solar_panel, 'solar_inverter':solar_inverter, 'peak_watt':peak_watt, 'latitude':latitude, 'longitude':longitude, 'message':message, 'rpi':rpi}

def sleeptimer():
	energy_left = (energy_reporting_increment - (energy_log['end_energy'] - energy_log['start_energy'])) * 1000
	print ("Waiting for another {:.3f} kWh to be generated, will check again in {:.0f} seconds (approx {:.2f} days)") .format(energy_left, inverter_query_increment, (inverter_query_increment/86400))
	print ("******** "+manufacturer_attribution+" ********")
	time.sleep(inverter_query_increment)

def slraddresstest():
	while True:
		solarcoin_address = raw_input ("What is your own SolarCoin Address: ")
		output = subprocess.check_output(['solarcoind', 'validateaddress', solarcoin_address], shell=False)[18:-3]
		if output != 'false':
			return solarcoin_address
		else:
			print ("********ERROR: SolarCoin address invlaid, check and try again *******")

def timestamp():
	now_time = time.strftime("%c", time.localtime())
	print ("*** {} Starting Datalogger Cycle  ***") .format(now_time)

def writetoblockchain():
	tx_message = str('{"module":"'+comm_creds['solar_panel']+'","inverter":"'+comm_creds['solar_inverter']+'","data-logger":"","pyranometer":"","windsensor":"","rainsensor":"","waterflow":"","Web_layer_API":"","Size_kW":"'
	+comm_creds['peak_watt']+'","lat":"'+comm_creds['latitude']+'","long":"'+comm_creds['longitude']+'","Comment":"'+comm_creds['message']+'","IoT":"'
	+comm_creds['rpi']+'","period":"{};{}","MWh":"{}"' .format(energy_log['start_time'], energy_log['end_time'], total_energy)+'} '+manufacturer_attribution)
	print("Initiating SolarCoin.....  TXID:")
	subprocess.call(['solarcoind', 'walletlock'], shell=False)
	subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999'], shell=False)
	subprocess.call(['solarcoind', 'sendtoaddress', comm_creds['solarcoin_address'], send_amount, '', '', tx_message], shell=False)
	subprocess.call(['solarcoind', 'walletlock'], shell=False)
	subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999', 'true'], shell=False)

solarcoin_passphrase = passphrasetest()
calculateamounttosend()
if os.path.isfile("LED.db"):
	print "Found LED database"
	dbname = "LED.db"
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute('''DROP TABLE IF EXISTS ENERGYLOG''')
	conn.commit()
	conn.close()
else:
	print "No database found, please complete the following credentials: "
	solarcoin_address = slraddresstest()
	solar_panel = raw_input ("What is the Make, Model & Part Number of your solar panel: ")
	solar_inverter = raw_input ("What is the Make, Model & Part Number of your inverter: ")
	peak_watt = peakwatttest()
	latitude = latitudetest()
	longitude = longitudetest()
	message = raw_input ("Add an optional message describing your system: ")
	rpi = raw_input ("If you are staking on a Raspberry Pi note the Model: ")
	databasecreate()

total_energy = float(raw_input ("In kWh (kilo-Watt hours) what is the start reading on your Solar PV meter: "))/1000
current_energy=0
energy_log = maintainenergylog()
comm_creds = retrievecommoncredentials()
print ("Waiting for {} kWh of energy to be generated") .format(energy_reporting_increment * 1000)

gpio.add_event_detect(17, gpio.RISING, callback=currentenergycounter, bouncetime=700)

while True:
	if current_energy >= energy_reporting_increment:
		total_energy = total_energy + current_energy
		print 'Reporting Total Energy {} MWh'.format (total_energy/1000)
		timestamp()
		energy_log = maintainenergylog()
		send_amount = calculateamounttosend()
		writetoblockchain()
		current_energy=0
		refreshenergylogandsleep()
		print ("Waiting for {} kWh of energy to be generated") .format(energy_reporting_increment * 1000)
