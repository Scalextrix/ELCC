#!/usr/bin/env python

"""datalogger.py: Queries the solar PV datalogger device on LAN or web, pulls production data and 
instructs the solarcoin daemon to make a transaction to record onto blockchain"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "4.2"

import gc
import getpass
import hashlib
import json
import os.path
import random
import subprocess
import sqlite3
import sys
import time
import urllib2
import uuid

energy_reporting_increment = 0.01 # Sets the frequency with which the reports will be made to block-chain, value in MWh e.g. 0.01 = 10kWh
manufacturer_attribution = "Powered by Enphase Energy: https://enphase.com"
api_key = "6ba121cb00bcdafe7035d57fe623cf1c&usf1c&usf1c"

def calculateamounttosend():
	try:
		utxos = json.loads(subprocess.check_output(['solarcoind', 'listunspent'], shell=False))
		for u in utxos:
       			amounts = [u['amount'] for u in utxos]
		wallet_balance = float(subprocess.check_output(['solarcoind', 'getbalance'], shell=False))
		if wallet_balance < 0.0005:
			print ("*******ERROR: wallet balance of {}SLR too low for reliable datalogging, add more SLR to wallet *******") .format(wallet_balance)
			time.sleep(10)
			sys.exit()
		elif wallet_balance >= 0.1:
			small_amounts = [i for i in amounts if i >=0.01 and i <=0.1]
			if len(small_amounts) == 0:
				tiny_amounts = [i for i in amounts if i <0.01]
				send_amount = str(sum(tiny_amounts))
				if send_amount < 0.01:
					send_amount = str(sum(tiny_amounts) + 0.01)
			else:
				send_amount = str(float(str(random.sample(small_amounts, 1))[1:-1])-0.0001)
			print ('Based on wallet balance of {} amount to send to self set to any amount between 0.01 & 0.1 SLR') .format(wallet_balance)
		else:
			send_amount = str(max([i for i in amounts]))
			print ("*******WARNING: low wallet balance of {}SLR, low send amount may result in higher TX fees*******") .format(wallet_balance)
		return send_amount
	except subprocess.CalledProcessError:
		print ("SolarCoin daemon offline, attempting restart, then sleeping for 5 minutes")
		subprocess.call(['solarcoind'], shell=False)
		time.sleep(300)
		return calculateamounttosend()

def databasecreate():
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS SYSTEMDETAILS (dataloggerid BLOB, systemid TEXT, userid TEXT, envoyip TEXT, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT)''')
	c.execute("INSERT INTO SYSTEMDETAILS VALUES (?,?,?,?,?,?,?,?,?,?,?);", (datalogger_id, system_id, user_id, envoy_ip, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi,))
	conn.commit()
	conn.close()

def databasenamebroken():
	del solarcoin_passphrase
	gc.collect()
	print "*******ERROR: Exiting in 10 seconds: Database name corrupted, delete *.db file and try again *******"
	time.sleep(10)
	sys.exit()

def inverterqueryincrement():
	""" Sets the frequency that the solar inverter is queried, value in Seconds; max 300 seconds set to stay within
	Enphase free Watt plan https://developer.enphase.com/plans """
	system_watt = float(comm_creds['peak_watt'])
	if system_watt <= 144:
		inverter_query_increment = int(86400/2/system_watt)
	else:
		inverter_query_increment = 300
	#inverter_query_increment = 300 # Uncomment for testing
	return inverter_query_increment

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
		subprocess.check_output(['solarcoind', 'walletlock'], shell=False)
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

def refreshenergylog():
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

def retrievecommoncredentials():
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	datalogger_id = str(c.execute('select dataloggerid from SYSTEMDETAILS').fetchone()[0])
	system_id = str(c.execute('select systemid from SYSTEMDETAILS').fetchone()[0])
	user_id = str(c.execute('select userid from SYSTEMDETAILS').fetchone()[0])
	envoy_ip = str(c.execute('select envoyip from SYSTEMDETAILS').fetchone()[0])
	solar_panel = str(c.execute('select panelid from SYSTEMDETAILS').fetchone()[0])
	solar_inverter = str(c.execute('select inverterid from SYSTEMDETAILS').fetchone()[0])
	peak_watt = str(c.execute('select pkwatt from SYSTEMDETAILS').fetchone()[0])
	latitude = str(c.execute('select lat from SYSTEMDETAILS').fetchone()[0])
	longitude = str(c.execute('select lon from SYSTEMDETAILS').fetchone()[0])
	message = str(c.execute('select msg from SYSTEMDETAILS').fetchone()[0])
	rpi = str(c.execute('select pi from SYSTEMDETAILS').fetchone()[0])
	conn.close()
	return {'datalogger_id':datalogger_id, 'system_id':system_id, 'user_id':user_id, 'envoy_ip':envoy_ip, 'solar_panel':solar_panel, 'solar_inverter':solar_inverter, 'peak_watt':peak_watt, 'latitude':latitude, 'longitude':longitude, 'message':message, 'rpi':rpi}

def sleeptimer():
	print ("******** "+manufacturer_attribution+" ********")
	time.sleep(inverter_query_increment)

def timestamp():
	now_time = time.strftime("%c", time.localtime())
	print ("*** {} Starting Datalogger Cycle  ***") .format(now_time)

def urltestandjsonload():
	print "Attempting Inverter API call and JSON data load"
	try:
		json_data = json.load(urllib2.urlopen(url, timeout=20))
	except urllib2.URLError, e:
		print ("******** ERROR: {} Sleeping for 5 minutes *******") .format(e)
		time.sleep(300)
		return urltestandjsonload()
	else:
		return json_data

def writetoblockchain():
	try:
		tx_message = str('{"UserID":"'+comm_creds['datalogger_id']+'","module":"'+comm_creds['solar_panel']+'","inverter":"'+comm_creds['solar_inverter']+'","data-logger":"","pyranometer":"","windsensor":"","rainsensor":"","waterflow":"","Web_layer_API":"","Size_kW":"'
		+comm_creds['peak_watt']+'","lat":"'+comm_creds['latitude']+'","long":"'+comm_creds['longitude']+'","Comment":"'+comm_creds['message']+'","IoT":"'
		+comm_creds['rpi']+'","period":"{};{}","Total MWh":"{}"' .format(energy_log['start_time'], energy_log['end_time'], total_energy)+'} '+manufacturer_attribution)		 
		print("Initiating SolarCoin.....  TXID:")
		solarcoin_address = str(subprocess.check_output(['solarcoind', 'getnewaddress'], shell=False))
		subprocess.call(['solarcoind', 'walletlock'], shell=False)
		subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999'], shell=False)
		subprocess.call(['solarcoind', 'sendtoaddress', solarcoin_address, send_amount, '', '', tx_message], shell=False)
		subprocess.call(['solarcoind', 'walletlock'], shell=False)
		subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999', 'true'], shell=False)
		refreshenergylog()
	except subprocess.CalledProcessError as e:
		print e.output

solarcoin_passphrase = passphrasetest()
calculateamounttosend()

if os.path.isfile("APIlan.db"):
	print "Found API LAN database"
	dbname = "APIlan.db"
elif os.path.isfile("APIweb.db"):
	print "Found API web database"
	dbname = "APIweb.db"
else:
	print "No database found, please complete the following credentials: "
	datalogger_id = hashlib.sha1(uuid.uuid4().hex).hexdigest()
	solar_panel = raw_input ("What is the Make, Model & Part Number of your solar panel: ")
	solar_inverter = raw_input ("What is the Make, Model & Part Number of your inverter: ")
	peak_watt = peakwatttest()
	latitude = latitudetest()
	longitude = longitudetest()
	message = raw_input ("Add an optional message describing your system: ")
	rpi = raw_input ("If you are staking on a Raspberry Pi note the Model: ")
	lan_web = raw_input ("Is the Inverter on your LAN: ").lower()
	if lan_web == "y" or lan_web == "yes" or lan_web == "lan":
		dbname="APIlan.db"
		system_id = ""
		user_id = ""
		envoy_ip = raw_input ("What is the IP address of your Inverter: ")
		databasecreate()
	elif lan_web == "n" or lan_web == "no" or lan_web == "web":
		dbname="APIweb.db"
		system_id = raw_input ("What is your Enphase System ID: ")
		user_id = raw_input ("What is your Enphase User ID: ")
		envoy_ip = ""
		databasecreate()
	else:
		del solarcoin_passphrase
		gc.collect()
		print "Exiting in 10 seconds: You must choose 'y' or 'n'"
		time.sleep(10)
		sys.exit()

comm_creds = retrievecommoncredentials()
inverter_query_increment = float(inverterqueryincrement())
while True:
	try:
		print ("---------- Press CTRL + c at any time to stop the Datalogger ----------")
		timestamp()
		if os.path.isfile("APIlan.db"):
			url = ("http://"+comm_creds['envoy_ip']+"/api/v1/production")
			json_data = urltestandjsonload()
			total_energy = float(json_data['wattHoursLifetime'])/1000000
		elif os.path.isfile("APIweb.db"):
			url = ("https://api.enphaseenergy.com/api/v2/systems/"+comm_creds['system_id']+"/summary?&key="+api_key+"&user_id="+comm_creds['user_id'])
			json_data = urltestandjsonload()
			total_energy = (float(json_data['energy_lifetime']) + float(json_data['energy_today'])) / 1000000
		else:
			databasenamebroken()

		print("Inverter API call successful: Total Energy MWh: {:.6f}") .format(total_energy)
		energy_log = maintainenergylog()

		if energy_log['end_energy'] >= (energy_log['start_energy'] + energy_reporting_increment):
			send_amount = calculateamounttosend()
			writetoblockchain()
			print ("Waiting {:.0f} seconds (approx {:.2f} days)") .format(inverter_query_increment, (inverter_query_increment/86400))
			sleeptimer()		
		else:
			energy_left = (energy_reporting_increment - (energy_log['end_energy'] - energy_log['start_energy'])) * 1000					
			print ("Waiting for another {:.3f} kWh to be generated, will check again in {:.0f} seconds (approx {:.2f} days)") .format(energy_left, inverter_query_increment, (inverter_query_increment/86400))
			sleeptimer()

	except KeyboardInterrupt:
       		del solarcoin_passphrase
       		gc.collect()
		print("Stopping Datalogger in 10 seconds")
		time.sleep(10)
		sys.exit()
