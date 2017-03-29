#!/usr/bin/env python

"""datalogger.py: Queries the solar PV datalogger device on LAN or web, pulls production data and 
instructs the solarcoin daemon to make a transaction to record onto blockchain"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "2.2"

import gc
import getpass
import json
import os.path
import subprocess
import sqlite3
import sys
import time
import urllib2

def calculateamounttosend():
        wallet_balance = float(subprocess.check_output(['solarcoind', 'getbalance'], shell=False))
        if wallet_balance >= 1000:
                send_amount = str(1)
        elif wallet_balance < 1000 and wallet_balance >= 10:
                send_amount = str(0.01)
        else:
                send_amount = str(0.00001)
        print ('Based on wallet balance of {} amount to send to self set to {} SLR') .format(wallet_balance, send_amount)
        return send_amount

def inverterqueryincrement():
        """ Sets the frequency that the solar inverter is queried, value in Seconds; max 300 seconds set to stay within
	Enphase free Watt plan https://developer.enphase.com/plans """
        system_watt = float(comm_creds['peak_watt'])
        if system_watt <= 288:
                inverter_query_increment = int(86400 / system_watt)
        else:
                inverter_query_increment = 300
        return inverter_query_increment

def maintainenergylog():
        conn = sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL)''')
        c.execute("INSERT INTO ENERGYLOG VALUES (NULL,?);", (total_energy,))
        conn.commit()
        row_count = c.execute('select max(id) FROM ENERGYLOG').fetchone()[0]
        start_energy = float(c.execute('select totalenergy from ENERGYLOG').fetchone()[0])
        end_energy = float(c.execute('select totalenergy from ENERGYLOG where id={}'.format(row_count)).fetchone()[0])
        conn.close()
        return{'start_energy':start_energy, 'end_energy':end_energy}

def refreshenergylogandsleep():
        conn= sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute('''DROP TABLE IF EXISTS ENERGYLOG''')
        conn.commit()
        c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL)''')
        c.execute("INSERT INTO ENERGYLOG VALUES (NULL,?);", (total_energy,))
        conn.commit()
        conn.close()
        print ("Waiting {:.0f} seconds (approx {:.2f} days)") .format(inverter_query_increment, (inverter_query_increment/86400))
        time.sleep(inverter_query_increment)

def retrievecommoncredentials():
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
	time.sleep(inverter_query_increment)

def timestamp():
	now_time = time.strftime("%a, %d %b %Y %H:%M:%S ", time.localtime())
	print ("*** {} Calling Inverter API  ***") .format(now_time)

def urltest():
	try:
		inverter = urllib2.urlopen(url, timeout = 20)
		return inverter
	except urllib2.URLError, e:
		print ("There was an error, exit in 10 seconds: {}") .format(e)
		time.sleep(10)
		sys.exit()

def writetoblockchain():
	tx_message = str('Note this is all public information '+comm_creds['solar_panel']+'; '+comm_creds['solar_inverter']+'; '+comm_creds['peak_watt']+'kW ;'+comm_creds['latitude']+','+comm_creds['longitude']+'; '+comm_creds['message']+'; '+comm_creds['rpi']+'; Total MWh: {}' .format(total_energy)+'; '+enphase_attribution)'
	print("Initiating SolarCoin")
	print("SolarCoin TXID:")
	subprocess.call(['solarcoind', 'walletlock'], shell=False)
	subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999'], shell=False)
	subprocess.call(['solarcoind', 'sendtoaddress', comm_creds['solarcoin_address'], send_amount, '', '', tx_message], shell=False)
	subprocess.call(['solarcoind', 'walletlock'], shell=False)
	subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999', 'true'], shell=False)

# Sets the frequency with which the reports will be made to block-chain, value in MWh e.g. 0.01 = 10kWh
energy_reporting_increment = 0.01

enphase_attribution = "Powered by Enphase Energy: https://enphase.com"

solarcoin_passphrase = getpass.getpass(prompt="What is your SolarCoin Wallet Passphrase: ")
print "Testing SolarCoin Wallet Passphrase, locking wallet..."
try:
	subprocess.call(['solarcoind', 'walletlock'], shell=False)
	subprocess.check_output(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999', 'true'], shell=False)
except subprocess.CalledProcessError:
	print "Incorrect Passphrase: Exiting in 10 seconds, SOLARCOIN WALLET NOT STAKING"
        time.sleep(10)
	sys.exit()
else:
        print "SolarCoin Wallet Passphrase correct, wallet unlocked for staking"
	
if os.path.isfile("APIlan.db"):
	lan_wan = "y"	
elif os.path.isfile("APIweb.db"):
	lan_wan = "n"
else:
	lan_wan = raw_input("Is the Enphase Envoy on your LAN: ").lower()

if lan_wan == "y" or lan_wan == "yes" or lan_wan == "lan":
	dbname="APIlan.db"
	if os.path.isfile(dbname):
		print("Found Enphase API LAN database")
	else:
		envoy_ip = raw_input ("What is your Enphase Envoy IP address: ")
		solarcoin_address = raw_input ("What is your SolarCoin Address: ")
		solar_panel = raw_input ("What is the Make, Model & Part Number of your solar panel: ")
		solar_inverter = raw_input ("What is the Make, Model & Part Number of your inverter: ")
		while True:
			peak_watt = raw_input ("In kW (kilo-Watts), what is the peak output of your system: ")
			try:
				peak_watt = float(peak_watt)
				break
			except ValueError:
				print "Error: You must enter numbers and decimal point only e.g. 3.975"
		latitude = raw_input ("What is the Latitude of your installation: ")
		longitude = raw_input ("What is the Longitude of your installation: ")
		message = raw_input ("Add an optional message describing your system: ")
		rpi = raw_input ("If you are staking on a Raspberry Pi note the Model: ")
		conn = sqlite3.connect(dbname)
		c = conn.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS SYSTEMDETAILS (envoyip TEXT, SLRaddress TEXT, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT)''')
		c.execute("INSERT INTO SYSTEMDETAILS VALUES (?,?,?,?,?,?,?,?,?);", (envoy_ip, solarcoin_address, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi,))
		conn.commit()		
		conn.close()

	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	envoy_ip = str(c.execute('select envoyip from SYSTEMDETAILS').fetchone()[0])
	comm_creds = retrievecommoncredentials()
	
        inverter_query_increment = float(inverterqueryincrement())
	
	while True:
		timestamp()
		url = ("http://"+envoy_ip+"/api/v1/production")
                inverter = urltest()

		print("Loading JSON data")
		data = json.load(inverter)
		total_energy = float(data['wattHoursLifetime'])/1000000
		print("Total Energy MWh: {:.6f}") .format(total_energy)

		energy_log = maintainenergylog()

		if energy_log['end_energy'] >= (energy_log['start_energy'] + energy_reporting_increment):
                        send_amount = calculateamounttosend()
			
			writetoblockchain()
			print enphase_attribution
			
			refreshenergylogandsleep()
		else:
			sleeptimer()	
	
elif lan_wan == "n" or lan_wan == "no" or lan_wan == "web":
	dbname="APIweb.db"
	api_key = ("6ba121cb00bcdafe7035d57fe623cf1c&usf1c&usf1c")
	if os.path.isfile(dbname):
		print("Found Enphase API web database")
	else:
		system_id = raw_input ("What is your Enphase System ID: ")
		user_id = raw_input ("What is your Enphase User ID: ")
		solarcoin_address = raw_input ("What is your SolarCoin Address: ")
		solar_panel = raw_input ("What is the Make, Model & Part Number of your solar panel: ")
		solar_inverter = raw_input ("What is the Make, Model & Part Number of your inverter: ")
		while True:
			peak_watt = raw_input ("In kW (kilo-Watts), what is the peak output of your system: ")
			try:
				peak_watt = float(peak_watt)
				break
			except ValueError:
				print "Error: You must enter numbers and decimal point only e.g. 3.975"
		latitude = raw_input ("What is the Latitude of your installation: ")
		longitude = raw_input ("What is the Longitude of your installation: ")
		message = raw_input ("Add an optional message describing your system: ")
		rpi = raw_input ("If you are staking on a Raspberry Pi note the Model: ")
		conn = sqlite3.connect(dbname)
		c = conn.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS SYSTEMDETAILS (systemid TEXT, userid TEXT, SLRaddress TEXT, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT)''')
		c.execute("INSERT INTO SYSTEMDETAILS VALUES (?,?,?,?,?,?,?,?,?,?);", (system_id, user_id, solarcoin_address, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi,))
		conn.commit()		
		conn.close()

	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	system_id = str(c.execute('select systemid from SYSTEMDETAILS').fetchone()[0])
	user_id = str(c.execute('select userid from SYSTEMDETAILS').fetchone()[0])
	comm_creds = retrievecommoncredentials()

        inverter_query_increment = float(inverterqueryincrement())
	
	while True:
		timestamp()
		url = ("https://api.enphaseenergy.com/api/v2/systems/"
		       +system_id+"/summary?&key="+api_key+"&user_id="+user_id)
                inverter = urltest()
		
		print("Loading JSON data")
		data = json.load(inverter)
		energy_lifetime = float(data['energy_lifetime'])
		energy_today = float(data['energy_today'])
		total_energy = (energy_lifetime + energy_today) / 1000000
		print("Total Energy MWh: {:.6f}") .format(total_energy)

		energy_log = maintainenergylog()
		
		if energy_log['end_energy'] >= (energy_log['start_energy'] + energy_reporting_increment):
                        send_amount = calculateamounttosend()

			writetoblockchain()
			print enphase_attribution
			
			refreshenergylogandsleep()		
		else:
			sleeptimer()

else:
	del solarcoin_passphrase
	gc.collect()
	print "Exiting in 10 seconds: You must choose 'y' or 'n'"
        time.sleep(10)
	sys.exit()
