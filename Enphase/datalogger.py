#!/usr/bin/env python

"""datalogger.py: Queries the solar PV datalogger device on LAN or web, pulls production data and 
instructs the solarcoin daemon to make a transaction to record onto blockchain"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "3.0"

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
	if wallet_balance < 0.0005:
		print ("Error: wallet balance of {}SLR too low for reliable datalogging, add more SLR to wallet") .format(wallet_balance)
		time.sleep(10)
		sys.exit
        elif wallet_balance >= 10:
                send_amount = str(1)
		print ('Based on wallet balance of {} amount to send to self set to {} SLR') .format(wallet_balance, send_amount)
        elif wallet_balance < 10 and wallet_balance >= 0.03:
                send_amount = str(0.01)
		print ('Based on wallet balance of {} amount to send to self set to {} SLR') .format(wallet_balance, send_amount)
        else:
                send_amount = str(0.00001)
		print ("Warning: low wallet balance of {}SLR, send amount of {} may result in higher TX fees") .format(wallet_balance, send_amount)
        return send_amount

def databasecreate():
        conn = sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS SYSTEMDETAILS (systemid TEXT, userid TEXT, envoyip TEXT, SLRaddress TEXT, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT)''')
        c.execute("INSERT INTO SYSTEMDETAILS VALUES (?,?,?,?,?,?,?,?,?,?,?);", (system_id, user_id, envoy_ip, solarcoin_address, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi,))
        conn.commit()
        conn.close()
	
def databasenamebroken():
        del solarcoin_passphrase
        gc.collect()
        print "Exiting in 10 seconds: Database name corrupted, delete *.db file and try again"
        time.sleep(10)
        sys.exit()

def inverterqueryincrement():
        """ Sets the frequency that the solar inverter is queried, value in Seconds; max 300 seconds set to stay within
	Enphase free Watt plan https://developer.enphase.com/plans """
        system_watt = float(comm_creds['peak_watt'])
        if system_watt <= 288:
                inverter_query_increment = int(86400 / system_watt)
        else:
                inverter_query_increment = 300
	# inverter_query_increment = 300 # Uncomment for testing
        return inverter_query_increment

def latitudetest():
        while True:
                latitude = raw_input ("What is the Latitude of your installation: ").upper()
                if latitude[-1] == 'N' or latitude[-1] == 'S':
                        try:
                                float(latitude[:-2])
                                return latitude
                        except ValueError:
                                print "Error: You must enter Latitude in a form 3.456N or 4.567S"
                else:
                        print "Error: You must enter Latitude in a form 3.456N or 4.567S"

def longitudetest():
        while True:
                longitude = raw_input ("What is the Longitude of your installation: ").upper()
                if longitude[-1] == 'E' or longitude[-1] == 'W':
                        try:
                                float(longitude[:-2])
                                return longitude
                        except ValueError:
                                print "Error: You must enter Longitude in a form 3.456E or 4.567W"
                else:
                        print "Error: You must enter Longitude in a form 3.456E or 4.567W"

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

def passphrasetest():
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
		return solarcoin_passphrase

def peakwatttest():
        while True:
                peak_watt = raw_input ("In kW (kilo-Watts), what is the peak output of your system: ")
                try:
                        peak_watt = float(peak_watt)
                        return peak_watt
                except ValueError:
                        print "Error: You must enter numbers and decimal point only e.g. 3.975"

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
        print ("******** "+manufacturer_attribution+" ********")
	time.sleep(inverter_query_increment)

def retrievecommoncredentials():
	conn = sqlite3.connect(dbname)
        c = conn.cursor()
        system_id = str(c.execute('select systemid from SYSTEMDETAILS').fetchone()[0])
        user_id = str(c.execute('select userid from SYSTEMDETAILS').fetchone()[0])
        envoy_ip = str(c.execute('select envoyip from SYSTEMDETAILS').fetchone()[0])
        solarcoin_address = str(c.execute('select SLRaddress from SYSTEMDETAILS').fetchone()[0])
        solar_panel = str(c.execute('select panelid from SYSTEMDETAILS').fetchone()[0])
        solar_inverter = str(c.execute('select inverterid from SYSTEMDETAILS').fetchone()[0])
        peak_watt = str(c.execute('select pkwatt from SYSTEMDETAILS').fetchone()[0])
        latitude = str(c.execute('select lat from SYSTEMDETAILS').fetchone()[0])
        longitude = str(c.execute('select lon from SYSTEMDETAILS').fetchone()[0])
        message = str(c.execute('select msg from SYSTEMDETAILS').fetchone()[0])
        rpi = str(c.execute('select pi from SYSTEMDETAILS').fetchone()[0])
        conn.close()
        return {'system_id':system_id, 'user_id':user_id, 'envoy_ip':envoy_ip, 'solarcoin_address':solarcoin_address, 'solar_panel':solar_panel, 'solar_inverter':solar_inverter, 'peak_watt':peak_watt, 'latitude':latitude, 'longitude':longitude, 'message':message, 'rpi':rpi}

def sleeptimer():
	energy_left = (energy_reporting_increment - (energy_log['end_energy'] - energy_log['start_energy'])) * 1000
	print ("Waiting for another {:.3f} kWh to be generated, will check again in {:.0f} seconds (approx {:.2f} days)") .format(energy_left, inverter_query_increment, (inverter_query_increment/86400))
	print ("******** "+manufacturer_attribution+" ********")
	time.sleep(inverter_query_increment)

def slraddresstest():
        while True:
                solarcoin_address = raw_input ("What is your SolarCoin Address: ")
                output = subprocess.check_output(['solarcoind', 'validateaddress', solarcoin_address], shell=False)[18:-3]
                if output != 'false':
                        return solarcoin_address
                else:
                        print ("Error: SolarCoin address invlaid, check and try again")

def timestamp():
	now_time = time.strftime("%a, %d %b %Y %H:%M:%S ", time.localtime())
	print ("*** {} Calling Inverter API  ***") .format(now_time)

def urltestandjsonload():
	print "Attempting Inverter API call and JSON data load"
	try:
		json_data = json.load(urllib2.urlopen(url, timeout=20))
	except urllib2.URLError, e:
		print ("There was an error, exit in 10 seconds: {}") .format(e)
		time.sleep(10)
		sys.exit()
	else:
                return json_data
	
def writetoblockchain():
	tx_message = str('Note this is all public information '+comm_creds['solar_panel']+'; '+comm_creds['solar_inverter']+'; '+comm_creds['peak_watt']+'kW ;'+comm_creds['latitude']+','+comm_creds['longitude']+'; '+comm_creds['message']+'; '+comm_creds['rpi']+'; Total MWh: {}' .format(total_energy)+'; '+manufacturer_attribution)
	print("Initiating SolarCoin.....  TXID:")
	subprocess.call(['solarcoind', 'walletlock'], shell=False)
	subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999'], shell=False)
	subprocess.call(['solarcoind', 'sendtoaddress', comm_creds['solarcoin_address'], send_amount, '', '', tx_message], shell=False)
	subprocess.call(['solarcoind', 'walletlock'], shell=False)
	subprocess.call(['solarcoind', 'walletpassphrase', solarcoin_passphrase, '9999999', 'true'], shell=False)

energy_reporting_increment = 0.01 # Sets the frequency with which the reports will be made to block-chain, value in MWh e.g. 0.01 = 10kWh
manufacturer_attribution = "Powered by Enphase Energy: https://enphase.com"
api_key = "6ba121cb00bcdafe7035d57fe623cf1c&usf1c&usf1c"

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
        solarcoin_address = slraddresstest()
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
                refreshenergylogandsleep()
        else:
                sleeptimer()
