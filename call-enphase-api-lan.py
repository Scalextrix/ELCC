#!/usr/bin/env python

"""call-enphase-api-lan.py: Queries the Enphase Envoy device on a LAN, pulls production data and instructs the solarcoin daemon to make a transaction to record onto blockchain"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.1"

import getpass
import os.path
import json
import subprocess
from urllib2 import urlopen
import sqlite3
import gc

solarcoin_passphrase = getpass.getpass(prompt="What is your SolarCoin Wallet Passphrase: ")

if os.path.isfile("APIlan.db"):
        print("Found Enphase API LAN database")
else:
	envoy_ip = raw_input ("What is your Enphase Envoy IP address: ")
	solarcoin_address = raw_input ("What is your SolarCoin Address: ")
	solar_panel = raw_input ("What is the Make, Model & Part Number of your solar panel: ")
        solar_inverter = raw_input ("What is the Make, Model & Part Number of your inverter: ")
	peak_watt = raw_input ("In kW (kilo-Watts), what is the peak output of your system: ")
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

print("Calling Enphase LAN API")
url = ("http://"+envoy_ip+"/api/v1/production")
inverter = urlopen(url)

print("Loading JSON data")
data = json.load(inverter)
energy_lifetime = data['wattHoursLifetime']
energy_today = data['wattHoursToday']
energy_lifetime = float(energy_lifetime)
energy_today = float(energy_today)
total_energy = (energy_lifetime + energy_today) / 1000000
print("Total Energy MWh: {:.6f}") .format(total_energy)

print("Initiating SolarCoin")
energylifetime = str('Note this is all public information '+solar_panel+'; '+solar_inverter+'; '+peak_watt+'kW ;'+latitude+','+longitude+'; '+message+'; '+rpi+'; Total MWh: {}' .format(total_energy)+'; Powered by Enphase Energy: http://enphase.com')
print("SolarCoin TXID:")
subprocess.call(['solarcoind', 'walletlock'], shell=False)
subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999'], shell=False)
subprocess.call(['solarcoind', 'sendtoaddress', solarcoin_address, '0.000001', '', '', energylifetime], shell=False)
subprocess.call(['solarcoind', 'walletlock'], shell=False)
subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999', 'true'], shell=False)
print("Powered by Enphase Energy: https://enphase.com")

del solarcoin_passphrase
gc.collect()
