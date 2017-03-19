#!/usr/bin/env python

"""datalogger.py: Queries the solar PV datalogger device on LAN or web, pulls production data and 
instructs the solarcoin daemon to make a transaction to record onto blockchain"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "2.1"

import gc
import getpass
import json
import os.path
import subprocess
import sqlite3
import sys
import time
from urllib2 import urlopen

# Sets the frequency with which the reports will be made to block-chain, value in MWh e.g. 0.01 = 10kWh
energy_reporting_increment = 0.01

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
	if os.path.isfile("APIlan.db"):
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
		conn = sqlite3.connect("APIlan.db")
		c = conn.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS SYSTEMDETAILS (envoyip TEXT, SLRaddress TEXT, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT)''')
		c.execute("INSERT INTO SYSTEMDETAILS VALUES (?,?,?,?,?,?,?,?,?);", (envoy_ip, solarcoin_address, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi,))
		conn.commit()		
		conn.close()

	conn = sqlite3.connect("APIlan.db")
	c = conn.cursor()
	envoy_ip = c.execute('select envoyip from SYSTEMDETAILS').fetchall()
	solarcoin_address = c.execute('select SLRaddress from SYSTEMDETAILS').fetchall()
	solar_panel = c.execute('select panelid from SYSTEMDETAILS').fetchall()
	solar_inverter = c.execute('select inverterid from SYSTEMDETAILS').fetchall()
	peak_watt = c.execute('select pkwatt from SYSTEMDETAILS').fetchall()
	latitude = c.execute('select lat from SYSTEMDETAILS').fetchall()
	longitude = c.execute('select lon from SYSTEMDETAILS').fetchall()
	message = c.execute('select msg from SYSTEMDETAILS').fetchall()
	rpi = c.execute('select pi from SYSTEMDETAILS').fetchall()
	conn.close()

	envoy_ip = str(envoy_ip[0][0])
	solarcoin_address = str(solarcoin_address[0][0])
	solar_panel = str(solar_panel[0][0])
	solar_inverter = str(solar_inverter[0][0])
	peak_watt = str(peak_watt[0][0])
	latitude = str(latitude[0][0])
	longitude = str(longitude[0][0])
	message = str(message[0][0])
	rpi = str(rpi[0][0])
	
	# Sets the frequency that the solar inverter is queried, value in Seconds
	system_watt = float(peak_watt)
	if system_watt <= 1000:
		inverter_query_increment = float(86400 / system_watt)
	else:
    		inverter_query_increment = 86

	while True:
		now_time = time.strftime("%a, %d %b %Y %H:%M:%S ", time.localtime())
		print ("*** {} Calling Enphase LAN API  ***") .format(now_time)
		url = ("http://"+envoy_ip+"/api/v1/production")
		inverter = urlopen(url)

		print("Loading JSON data")
		data = json.load(inverter)
		total_energy = data['wattHoursLifetime']
		total_energy = float(total_energy)
		total_energy = total_energy / 1000000
		print("Total Energy MWh: {:.6f}") .format(total_energy)

		conn = sqlite3.connect("APIlan.db")
		c = conn.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL)''')
		c.execute("INSERT INTO ENERGYLOG VALUES (NULL,?);", (total_energy,))
		conn.commit()		
		conn.close()

		conn = sqlite3.connect("APIlan.db")
		c = conn.cursor()
		row_count = c.execute('select max(id) FROM ENERGYLOG').fetchone()[0]
		start_energy = c.execute('select totalenergy from ENERGYLOG').fetchone()
		end_energy = c.execute('select totalenergy from ENERGYLOG where id={}'.format(row_count)).fetchone()
		conn.close()
		start_energy = str(start_energy)[1:-2]
		end_energy = str(end_energy)[1:-2]
		start_energy = float(start_energy)
		end_energy = float(end_energy)

		if end_energy >= (start_energy + energy_reporting_increment):
			print("Initiating SolarCoin")
			energylifetime = str('Note this is all public information '+solar_panel+'; '+solar_inverter+'; '+peak_watt+'kW ;'+latitude+','+longitude+'; '+message+'; '+rpi+'; Total MWh: {}' .format(total_energy)+'; Powered by Enphase Energy: http://enphase.com')
			print("SolarCoin TXID:")
			subprocess.call(['solarcoind', 'walletlock'], shell=False)
			subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999'], shell=False)
			subprocess.call(['solarcoind', 'sendtoaddress', solarcoin_address, '0.01', '', '', energylifetime], shell=False)
			subprocess.call(['solarcoind', 'walletlock'], shell=False)
			subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999', 'true'], shell=False)
			print("Powered by Enphase Energy: https://enphase.com")
			
			conn= sqlite3.connect("APIlan.db")
			c = conn.cursor()
			c.execute('''DROP TABLE IF EXISTS ENERGYLOG''')
			conn.commit()		
                        c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL)''')
                        c.execute("INSERT INTO ENERGYLOG VALUES (NULL,?);", (total_energy,))
                        conn.commit()
                        conn.close()

                        print ("Waiting {:.0f} seconds before checking again (approx {:.2F} days)") .format(inverter_query_increment, (inverter_query_increment/86400))
                        time.sleep(inverter_query_increment)
			gc.collect()
		else:
			energy_left = (energy_reporting_increment - (end_energy - start_energy)) * 1000
			print ("Waiting for another {:.3f} kWh to be generated, will check again in {:.0f} seconds (approx {:.2F} days)") .format(energy_left, inverter_query_increment, (inverter_query_increment/86400))
			time.sleep(inverter_query_increment)		
	
elif lan_wan == "n" or lan_wan == "no" or lan_wan == "web":
	api_key = ("6ba121cb00bcdafe7035d57fe623cf1c&usf1c&usf1c")
	if os.path.isfile("APIweb.db"):
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
		conn = sqlite3.connect("APIweb.db")
		c = conn.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS SYSTEMDETAILS (systemid TEXT, userid TEXT, SLRaddress TEXT, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT)''')
		c.execute("INSERT INTO SYSTEMDETAILS VALUES (?,?,?,?,?,?,?,?,?,?);", (system_id, user_id, solarcoin_address, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi,))
		conn.commit()		
		conn.close()

	conn = sqlite3.connect("APIweb.db")
	c = conn.cursor()
	system_id = c.execute('select systemid from SYSTEMDETAILS').fetchall()
	user_id = c.execute('select userid from SYSTEMDETAILS').fetchall()
	solarcoin_address = c.execute('select SLRaddress from SYSTEMDETAILS').fetchall()
	solar_panel = c.execute('select panelid from SYSTEMDETAILS').fetchall()
	solar_inverter = c.execute('select inverterid from SYSTEMDETAILS').fetchall()
	peak_watt = c.execute('select pkwatt from SYSTEMDETAILS').fetchall()
	latitude = c.execute('select lat from SYSTEMDETAILS').fetchall()
	longitude = c.execute('select lon from SYSTEMDETAILS').fetchall()
	message = c.execute('select msg from SYSTEMDETAILS').fetchall()
	rpi = c.execute('select pi from SYSTEMDETAILS').fetchall()
	conn.close()

	system_id = str(system_id[0][0])
	user_id = str(user_id[0][0])
	solarcoin_address = str(solarcoin_address[0][0])
	solar_panel = str(solar_panel[0][0])
	solar_inverter = str(solar_inverter[0][0])
	peak_watt = str(peak_watt[0][0])
	latitude = str(latitude[0][0])
	longitude = str(longitude[0][0])
	message = str(message[0][0])
	rpi = str(rpi[0][0])
	
	# Sets the frequency that the solar inverter is queried, value in Seconds; max 300 seconds set to stay within Enphase free Watt plan https://developer.enphase.com/plans 
	system_watt = float(peak_watt)
	if system_watt <= 288:
		inverter_query_increment = float(86400 / system_watt)
	else:
    		inverter_query_increment = 300
		
	while True:
		now_time = time.strftime("%a, %d %b %Y %H:%M:%S ", time.localtime())
		print ("*** {} Calling Enphase web API ***") .format(now_time)
		url = ("https://api.enphaseenergy.com/api/v2/systems/"
		       +system_id+"/summary?&key="+api_key+"&user_id="+user_id)
		inverter = urlopen(url)

		print("Loading JSON data")
		data = json.load(inverter)
		energy_lifetime = data['energy_lifetime']
		energy_today = data['energy_today']
		energy_lifetime = float(energy_lifetime)
		energy_today = float(energy_today)
		total_energy = (energy_lifetime + energy_today) / 1000000
		print("Total Energy MWh: {:.6f}") .format(total_energy)

		conn = sqlite3.connect("APIweb.db")
		c = conn.cursor()
		c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL)''')
		c.execute("INSERT INTO ENERGYLOG VALUES (NULL,?);", (total_energy,))
		conn.commit()		
		conn.close()

		conn = sqlite3.connect("APIweb.db")
		c = conn.cursor()
		row_count = c.execute('select max(id) FROM ENERGYLOG').fetchone()[0]
		start_energy = c.execute('select totalenergy from ENERGYLOG').fetchone()
		end_energy = c.execute('select totalenergy from ENERGYLOG where id={}'.format(row_count)).fetchone()
		conn.close()
		start_energy = str(start_energy)[1:-2]
		end_energy = str(end_energy)[1:-2]
		start_energy = float(start_energy)
		end_energy = float(end_energy)
		
		if end_energy >= (start_energy + energy_reporting_increment):
			print("Initiating SolarCoin")
			energylifetime = str('Note this is all public information '+solar_panel+'; '+solar_inverter+'; '+peak_watt+'kW ;'+latitude+','+longitude+'; '+message+'; '+rpi+'; Total MWh: {}' .format(total_energy)+'; Powered by Enphase Energy: http://enphase.com')
			print("SolarCoin TXID:")
			subprocess.call(['solarcoind', 'walletlock'], shell=False)
			subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999'], shell=False)
			subprocess.call(['solarcoind', 'sendtoaddress', solarcoin_address, '0.01', '', '', energylifetime], shell=False)
			subprocess.call(['solarcoind', 'walletlock'], shell=False)
			subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999', 'true'], shell=False)
			print("Powered by Enphase Energy: https://enphase.com")
			
			conn= sqlite3.connect("APIweb.db")
			c = conn.cursor()
			c.execute('''DROP TABLE IF EXISTS ENERGYLOG''')
			conn.commit()		
                        c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL)''')
                        c.execute("INSERT INTO ENERGYLOG VALUES (NULL,?);", (total_energy,))
                        conn.commit()
                        conn.close()

                        print ("Waiting {:.0f} seconds before checking again (approx {:.2f} days") .format(inverter_query_increment, (inverter_query_increment/86400))
                        time.sleep(inverter_query_increment)
			gc.collect()			
		else:
			energy_left = (energy_reporting_increment - (end_energy - start_energy)) * 1000
			print ("Waiting for another {:.3f} kWh to be generated, will check again in {:.0f} seconds (approx {:.2f} days)") .format(energy_left, inverter_query_increment, (inverter_query_increment/86400))
			time.sleep(inverter_query_increment)

else:
	del solarcoin_passphrase
	gc.collect()
	print "Exiting in 10 seconds: You must choose 'y' or 'n'"
        time.sleep(10)
	sys.exit()
