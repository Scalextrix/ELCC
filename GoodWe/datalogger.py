#!/usr/bin/env python

"""datalogger.py: Queries the solar PV datalogger device on LAN or web, pulls production data and 
instructs the solarcoin daemon to make a transaction to record onto blockchain"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "6.1"

import gc
import getpass
import hashlib
import json
from lxml import html
import os.path
import random
import requests
import socket
import sqlite3
import sys
import time
import urllib2
import uuid

energy_reporting_increment = 0.01 # Sets the frequency with which the reports will be made to block-chain, value in MWh e.g. 0.01 = 10kWh
manufacturer_attribution = ""
api_key = ""

def azimuthtest():
	while True:
		azimuth = raw_input ("What is the Azimuth of your panels (0 degrees = Magnetic North), or 'tracked': ").lower()
                if azimuth == 'tracked':
			return azimuth
		else:
			try:
                        	azimuth_int = int(azimuth)
                        	if azimuth_int < 360 and azimuth_int >= 0:
                                	return azimuth
                        	else:
                                	print "*******ERROR: You must enter Azimuth as a number between 0 and 359, or 'tracked' *******"
                	except ValueError:
                        	print "*******ERROR: You must enter Azimuth as a number between 0 and 359, or 'tracked' *******"

def calculateamounttosend():
	utxos = instruct_wallet('listunspent', [])['result']		
	for u in utxos:
		amounts = [u['amount'] for u in utxos]
	wallet_balance = float(instruct_wallet('getbalance', [])['result'])		
	if wallet_balance < 0.0005:
		print ("*******ERROR: wallet balance of {}SLR too low for reliable datalogging, add more SLR to wallet *******") .format(wallet_balance)
		time.sleep(10)
		sys.exit()
	elif wallet_balance >= 0.1:
		small_amounts = [i for i in amounts if i >=0.01 and i <=0.1]
		if len(small_amounts) == 0:
			tiny_amounts = [i for i in amounts if i <0.01]
			send_amount = float(sum(tiny_amounts))
			if send_amount < 0.01:
				send_amount = float(sum(tiny_amounts) + 0.01)
		else:
			send_amount = float(str(random.sample(small_amounts, 1))[1:-1])-0.0001
		print ('Based on wallet balance of {} amount to send to self set to any amount between 0.01 & 0.1 SLR') .format(wallet_balance)
	else:
		send_amount = float(max([i for i in amounts]))
		print ("*******WARNING: low wallet balance of {}SLR, low send amount may result in higher TX fees*******") .format(wallet_balance)
	return send_amount

def checksum():
	hasher = hashlib.sha1()
        with open('datalogger.py', 'rb') as afile:  
                buf = afile.read()
                hasher.update(buf)
        return (hasher.hexdigest())

def databasecreate():
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute('''DROP TABLE IF EXISTS SYSTEMDETAILS''')
	conn.commit()
	c.execute('''CREATE TABLE IF NOT EXISTS SYSTEMDETAILS (dataloggerid BLOB, systemid TEXT, userid TEXT, envoyip TEXT, panelid TEXT, tilt TEXT, azimuth TEXT, inverterid TEXT, datalogger TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, slrsigaddr BLOB)''')
	c.execute("INSERT OR REPLACE INTO SYSTEMDETAILS VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?);", (datalogger_id, system_id, user_id, envoy_ip, solar_panel, tilt, azimuth, solar_inverter, d_logger_type, peak_watt, latitude, longitude, message, solarcoin_sig_address,))
	conn.commit()
	conn.close()

def databasenamebroken():
	del solarcoin_passphrase
	gc.collect()
	print "*******ERROR: Exiting in 10 seconds: Database name corrupted, delete *.db file and try again *******"
	time.sleep(10)
	sys.exit()

def instruct_wallet(method, params):
	url = "http://127.0.0.1:18181/"
	payload = json.dumps({"method": method, "params": params})
	headers = {'content-type': "application/json", 'cache-control': "no-cache"}
	try:
		response = requests.request("POST", url, data=payload, headers=headers, auth=(rpc_user, rpc_pass))
		return json.loads(response.text)
	except requests.exceptions.RequestException as e:
		print e

def inverterqueryincrement():
	""" Sets the frequency that the solar inverter is queried, value in Seconds; set max 300 seconds set to stay within
	Enphase free Watt plan https://developer.enphase.com/plans """
	system_watt = float(comm_creds['peak_watt'])
	if system_watt <= 144:
		inverter_query_increment = int(86400/20/system_watt)
	else:
		inverter_query_increment = 30
	#inverter_query_increment = 30 # Uncomment for testing
	return inverter_query_increment

def lanenvoyserialfinder():
	page = requests.get('http://'+envoy_ip+'/home?locale=en')
	tree = html.fromstring(page.content)
	serial_number = str(tree.xpath('//td[2][@class="hdr_line"]/text()')[0][21:])
	return serial_number

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

def messagetest():
	while True:
		message = raw_input ("Add an optional message describing your system (max 40 characters): ")
		if len(message) > 40:
			print ('message too long by {} characters').format((len(message)-40))
		else:
			return message

def maintainenergylog():
	conn = sqlite3.connect(dbname)
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL UNIQUE, time REAL)''')
	now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
	c.execute("INSERT OR IGNORE INTO ENERGYLOG VALUES (NULL,?,?);", (total_energy, now_time))
	conn.commit()
	energy_list = [float(f[0]) for f in (c.execute('select totalenergy from ENERGYLOG').fetchall())]
	time_list = [str(f[0]) for f in (c.execute('select time from ENERGYLOG').fetchall())]
	conn.close()
	energy_list_length = len(energy_list)
	return {'energy_list':energy_list, 'time_list':time_list, 'energy_list_length':energy_list_length}

def passphrasetest():
	solarcoin_passphrase = getpass.getpass(prompt="What is your SolarCoin Wallet Passphrase: ")
	print "Testing SolarCoin Wallet Passphrase, locking wallet..."
	instruct_wallet('walletlock', [])
	answer = instruct_wallet('walletpassphrase', [solarcoin_passphrase, 9999999, True])
	if answer['error'] != None:
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
	c.execute('''CREATE TABLE IF NOT EXISTS ENERGYLOG (id INTEGER PRIMARY KEY AUTOINCREMENT, totalenergy REAL UNIQUE, time REAL)''')
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
	tilt = str(c.execute('select tilt from SYSTEMDETAILS').fetchone()[0])
	azimuth = str(c.execute('select azimuth from SYSTEMDETAILS').fetchone()[0])
	solar_inverter = str(c.execute('select inverterid from SYSTEMDETAILS').fetchone()[0])
	peak_watt = str(c.execute('select pkwatt from SYSTEMDETAILS').fetchone()[0])
	latitude = str(c.execute('select lat from SYSTEMDETAILS').fetchone()[0])
	longitude = str(c.execute('select lon from SYSTEMDETAILS').fetchone()[0])
	message = str(c.execute('select msg from SYSTEMDETAILS').fetchone()[0])
	d_logger_type = str(c.execute('select datalogger from SYSTEMDETAILS').fetchone()[0])
	solarcoin_sig_address = str(c.execute('select slrsigaddr from SYSTEMDETAILS').fetchone()[0])
	conn.close()
	return {'datalogger_id':datalogger_id, 'system_id':system_id, 'user_id':user_id, 'envoy_ip':envoy_ip, 'solar_panel':solar_panel, 'tilt':tilt, 'azimuth':azimuth, 'solar_inverter':solar_inverter, 'd_logger_type':d_logger_type, 'peak_watt':peak_watt, 'latitude':latitude, 'longitude':longitude, 'message':message, 'solarcoin_sig_address':solarcoin_sig_address}

def sleeptimer():
	print ("******** "+manufacturer_attribution+" ********")
	print''
	time.sleep(inverter_query_increment)

def tilttest():
	while True:
		tilt = raw_input ("What is the Tilt of your panels from horizontal (degrees): ")
		if tilt == 'tracked':
			return tilt
		else:
			try:
				tilt_int = int(tilt)
				if tilt_int <= 90 and tilt_int >= 0:
					return tilt
				else:
					print "*******ERROR: You must enter Tilt as a number between 0 and 90, or 'tracked' *******"
			except ValueError:
				print "*******ERROR: You must enter Tilt as a number between 0 and 90, or 'tracked' *******"

def timestamp():
	now_time = time.strftime("%c", time.localtime())
	print ("*** {} Starting Datalogger Cycle for UID {} ***") .format(now_time, comm_creds['datalogger_id'])

def urltestandjsonload(url):
	print "Attempting Inverter API call and JSON data load"
	try:
		json_data = json.load(urllib2.urlopen(url, timeout=20))
	except urllib2.URLError, e:
		print ("******** URL ERROR: {} Sleeping for 5 minutes *******") .format(e)
		time.sleep(300)
		return urltestandjsonload(url)
	except socket.timeout:
		print "******** SOCKET TIMEOUT: Sleeping for 5 minutes *******"
		time.sleep(300)
		return urltestandjsonload(url)
	except socket.error:
		print "******** SOCKET ERROR: Sleeping for 5 minutes then trying Inverter again *******"
		time.sleep(300)
		return urltestandjsonload(url)
	else:
		return json_data

def webenvoyserialfinder():
	url = ("https://api.enphaseenergy.com/api/v2/systems/"+system_id+"/envoys?&key="+api_key+"&user_id="+user_id)
	json_data = urltestandjsonload(url)
	serial_number = str(json_data['envoys'][0]['serial_number'])
	return serial_number

def writetoblockchaingen():
	time1=energy_log['time_list'][int(energy_log['energy_list_length']*0.125)]
	energy1=energy_log['energy_list'][int(energy_log['energy_list_length']*0.125)]
	time2=energy_log['time_list'][int(energy_log['energy_list_length']*0.25)]
	energy2=energy_log['energy_list'][int(energy_log['energy_list_length']*0.25)]
	time3=energy_log['time_list'][int(energy_log['energy_list_length']*0.375)]
	energy3=energy_log['energy_list'][int(energy_log['energy_list_length']*0.375)]
	time4=energy_log['time_list'][int(energy_log['energy_list_length']*0.5)]
	energy4=energy_log['energy_list'][int(energy_log['energy_list_length']*0.5)]
        time5=energy_log['time_list'][int(energy_log['energy_list_length']*0.625)]
        energy5=energy_log['energy_list'][int(energy_log['energy_list_length']*0.625)]
        time6=energy_log['time_list'][int(energy_log['energy_list_length']*0.75)]
        energy6=energy_log['energy_list'][int(energy_log['energy_list_length']*0.75)]
        time7=energy_log['time_list'][int(energy_log['energy_list_length']*0.875)]
        energy7=energy_log['energy_list'][int(energy_log['energy_list_length']*0.875)]
	time8=energy_log['time_list'][-1]
	energy8=energy_log['energy_list'][-1]
	retrievecommoncredentials()

	tx_message = str('{"UID":"'+comm_creds['datalogger_id']
	+'","t0":"{}","MWh0":{}' .format(time1, energy1)
	+',"t1":"{}","MWh1":{}' .format(time2, energy2)
	+',"t2":"{}","MWh2":{}' .format(time3, energy3)
	+',"t3":"{}","MWh3":{}' .format(time4, energy4)
	+',"t4":"{}","MWh4":{}' .format(time5, energy5)
	+',"t5":"{}","MWh5":{}' .format(time6, energy6)
	+',"t6":"{}","MWh6":{}' .format(time7, energy7)
	+',"t7":"{}","MWh7":{}' .format(time8, energy8)+'}')
	checksum_tx_message = tx_message+checksum
	instruct_wallet('walletlock', [])
	instruct_wallet('walletpassphrase', [solarcoin_passphrase, 9999999])
	sig_hash = str(instruct_wallet('signmessage', [comm_creds['solarcoin_sig_address'], checksum_tx_message])['result'])
	hash_tx_message = str('genv1'+tx_message+'Sig:'+sig_hash) 
	print("Initiating SolarCoin.....  TXID:")
	solarcoin_address = str(instruct_wallet('getnewaddress', [])['result'])
	print instruct_wallet('sendtoaddress', [solarcoin_address, send_amount, '', '', hash_tx_message])['result']
	instruct_wallet('walletlock', [])
	instruct_wallet('walletpassphrase', [solarcoin_passphrase, 9999999, True])
	refreshenergylog()	

def writetoblockchainsys():
	retrievecommoncredentials()
	tx_message = str('{"UID":"'+comm_creds['datalogger_id']
	+'","SigAddr":"'+comm_creds['solarcoin_sig_address']
	+'","module":"'+comm_creds['solar_panel']
	+'","tilt":"'+comm_creds['tilt']
	+'","azimuth":"'+comm_creds['azimuth']
	+'","inverter":"'+comm_creds['solar_inverter']
	+'","data-logger":"'+comm_creds['d_logger_type']
	+'","Size_kW":"'+comm_creds['peak_watt']
	+'","lat":"'+comm_creds['latitude']
	+'","long":"'+comm_creds['longitude']
	+'","Comment":"'+comm_creds['message']
	+'"}')
	checksum_tx_message = tx_message+checksum
	instruct_wallet('walletlock', [])
	instruct_wallet('walletpassphrase', [solarcoin_passphrase, 9999999])
	sig_hash = str(instruct_wallet('signmessage', [solarcoin_sig_address, checksum_tx_message])['result'])
	hash_tx_message = str('sysv1'+tx_message+'Sig:'+sig_hash)
	print("Writing System Details to Block-Chain..... TXID:")
	solarcoin_address = str(instruct_wallet('getnewaddress', [])['result'])
	print instruct_wallet('sendtoaddress', [solarcoin_address, send_amount, '', '', hash_tx_message])['result']
	instruct_wallet('walletlock', [])
	instruct_wallet('walletpassphrase', [solarcoin_passphrase, 9999999, True])
	print 'Waiting 5 minutes to allow System Details to be written to Block'
	time.sleep(300)

if os.name == 'nt':
	user_account = getpass.getuser()
	f = open('C:\Users\{}\AppData\Roaming\SolarCoin\SolarCoin.conf'.format(user_account), 'rb')
	for line in f:
		line = line.rstrip()
		if line[0:7] == 'rpcuser':
			rpc_user = line[line.find('=')+1:]
		if line[0:11] == 'rpcpassword':
			rpc_pass = line[line.find('=')+1:]
	f.close()
elif os.name == 'posix':
	homedir = os.environ['HOME']
	f = open(homedir+'/.solarcoin/solarcoin.conf', 'r')
	for line in f:
		line = line.rstrip()
		if line[0:7] == 'rpcuser':
			rpc_user = line[line.find('=')+1:]
		if line[0:11] == 'rpcpassword':
			rpc_pass = line[line.find('=')+1:]
	f.close()
else:
	print 'SolarCoin.conf not found, please ensure it is in the default location'
	time.sleep(10)
	sys.exit()

checksum = str(checksum())
solarcoin_passphrase = passphrasetest()
send_amount = calculateamounttosend()

if os.path.isfile("APIlansig.db"):
	print "Found API LAN database"
	dbname = "APIlansig.db"
	system_update_chooser = raw_input('Would you like to update your system information; Y/N?: ').upper()
	if system_update_chooser == 'Y':
		comm_creds = retrievecommoncredentials()
		print 'Current UID: {}'.format(comm_creds['datalogger_id'])
		solarcoin_sig_address = comm_creds['solarcoin_sig_address']
		print 'Solar Panel: {}'.format(comm_creds['solar_panel'])
		details_changer = raw_input ('Change Y/N?: ').lower()
		if details_changer == 'y':
			solar_panel = raw_input ("What is the Make, Model & Part Number of your solar panel: ")
		else:
			solar_panel = comm_creds['solar_panel']
		print 'Tilt: {}'.format(comm_creds['tilt'])
		details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
			tilt = tilttest()
		else:
			tilt = comm_creds['tilt']
		print 'Azimuth: {}'.format(comm_creds['azimuth'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
			azimuth = azimuthtest()
		else:
			azimuth = comm_creds['azimuth']
		print 'Inverter: {}'.format(comm_creds['solar_inverter'])
		details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
			solar_inverter = raw_input ("What is the Make, Model & Part Number of your inverter: ")
		else:
			solar_inverter = comm_creds['solar_inverter']
		print 'Data-logger: {}'.format(comm_creds['d_logger_type'])
		details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
			d_logger_type = raw_input ("What is the Make, Model & Part Number of your data-logging device: ")
		else:
			d_logger_type = comm_creds['d_logger_type']
		print 'Peak Watt: {}'.format(comm_creds['peak_watt'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
			peak_watt = peakwatttest()
		else:
			peak_watt = comm_creds['peak_watt']
		print 'Latitude: {}'.format(comm_creds['latitude'])
		details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
			latitude = latitudetest()
		else:
			latitude = comm_creds['latitude']
                print 'Longitude: {}'.format(comm_creds['longitude'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        longitude = longitudetest()
                else:
                        longitude = comm_creds['longitude']
                print 'Comment: {}'.format(comm_creds['message'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        message = messagetest()
                else:
                        message = comm_creds['message']
                print 'IP Address: {}'.format(comm_creds['envoy_ip'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        envoy_ip = raw_input ("What is the IP address of your Inverter: ")
                else:
                        envoy_ip = comm_creds['envoy_ip']
		system_id = ""
		user_id = ""
                envoy_serial_no = lanenvoyserialfinder()
                datalogger_id = hashlib.sha1(envoy_serial_no+solar_panel+str(tilt)+str(azimuth)+solar_inverter+d_logger_type+str(peak_watt)+latitude+longitude).hexdigest()
		databasecreate()
		comm_creds = retrievecommoncredentials()
		print 'New UID: {}'.format(comm_creds['datalogger_id'])
		writetoblockchainsys()
	else:
		print 'Continuing to look for energy'
elif os.path.isfile("APIwebsig.db"):
	print "Found API web database"
	dbname = "APIwebsig.db"
	system_update_chooser = raw_input('Would you like to update your system information; Y/N?: ').upper()
	if system_update_chooser == 'Y':
		comm_creds = retrievecommoncredentials()
		print 'Current UID: {}'.format(comm_creds['datalogger_id'])
		solarcoin_sig_address = comm_creds['solarcoin_sig_address']
                print 'Solar Panel: {}'.format(comm_creds['solar_panel'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        solar_panel = raw_input ("What is the Make, Model & Part Number of your solar panel: ")
                else:
                        solar_panel = comm_creds['solar_panel']
                print 'Tilt: {}'.format(comm_creds['tilt'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        tilt = tilttest()
                else:
                        tilt = comm_creds['tilt']
                print 'Azimuth: {}'.format(comm_creds['azimuth'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        azimuth = azimuthtest()
                else:
                        azimuth = comm_creds['azimuth']
                print 'Inverter: {}'.format(comm_creds['solar_inverter'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        solar_inverter = raw_input ("What is the Make, Model & Part Number of your inverter: ")
                else:
                        solar_inverter = comm_creds['solar_inverter']
                print 'Data-logger: {}'.format(comm_creds['d_logger_type'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        d_logger_type = raw_input ("What is the Make, Model & Part Number of your data-logging device: ")
                else:
                        d_logger_type = comm_creds['d_logger_type']
                print 'Peak Watt: {}'.format(comm_creds['peak_watt'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        peak_watt = peakwatttest()
                else:
                        peak_watt = comm_creds['peak_watt']
                print 'Latitude: {}'.format(comm_creds['latitude'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        latitude = latitudetest()
                else:
                        latitude = comm_creds['latitude']
                print 'Longitude: {}'.format(comm_creds['longitude'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        longitude = longitudetest()
                else:
                        longitude = comm_creds['longitude']
                print 'Comment: {}'.format(comm_creds['message'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        message = messagetest()
                else:
                        message = comm_creds['message']
                print 'System ID: {}'.format(comm_creds['system_id'])
                details_changer = raw_input ('Change Y/N?: ').lower()
                if details_changer == 'y':
                        system_id = raw_input ("What is your Enphase System ID: ")
                else:
                        system_id = comm_creds['system_id']
                user_id = ""
		envoy_ip = ""
                envoy_serial_no = raw_input ("What is your GoodWe Inverter Serial Number: ")
                datalogger_id = hashlib.sha1(envoy_serial_no+solar_panel+str(tilt)+str(azimuth)+solar_inverter+d_logger_type+str(peak_watt)+latitude+longitude).hexdigest()
                databasecreate()
		comm_creds = retrievecommoncredentials()
		print 'New UID: {}'.format(comm_creds['datalogger_id'])
		writetoblockchainsys()
	else:
		print 'Continuing to look for energy'
else:
	print "No database found, please complete the following credentials: "
	solarcoin_sig_address = str(instruct_wallet('getnewaddress', [])['result'])	
	solar_panel = raw_input ("What is the Make, Model & Part Number of your solar panel: ")
	tilt = tilttest()
	azimuth = azimuthtest()
	solar_inverter = raw_input ("What is the Make, Model & Part Number of your inverter: ")
	d_logger_type = raw_input ("What is the Make, Model & Part Number of your data-logging device: ")
	peak_watt = peakwatttest()
	latitude = latitudetest()
	longitude = longitudetest()
	message = messagetest()
	lan_web = raw_input ("Is the Inverter on your LAN: ").lower()
	if lan_web == "y" or lan_web == "yes" or lan_web == "lan":
		dbname="APIlansig.db"
		system_id = ""
		user_id = ""
		envoy_ip = raw_input ("What is the IP address of your Inverter: ")
		envoy_serial_no = lanenvoyserialfinder()
		datalogger_id = hashlib.sha1(envoy_serial_no+solar_panel+str(tilt)+str(azimuth)+solar_inverter+d_logger_type+str(peak_watt)+latitude+longitude).hexdigest()
		databasecreate()
		comm_creds = retrievecommoncredentials()
		print 'New UID: {}'.format(comm_creds['datalogger_id'])
		writetoblockchainsys()
	elif lan_web == "n" or lan_web == "no" or lan_web == "web":
		dbname="APIwebsig.db"
		system_id = raw_input ("What is your GoodWe System ID: ")
		user_id = ""
		envoy_ip = ""
                envoy_serial_no = raw_input ("What is your GoodWe Inverter Serial Number: ")
                datalogger_id = hashlib.sha1(envoy_serial_no+solar_panel+str(tilt)+str(azimuth)+solar_inverter+d_logger_type+str(peak_watt)+latitude+longitude).hexdigest()
		databasecreate()
		comm_creds = retrievecommoncredentials()
		print 'New UID: {}'.format(comm_creds['datalogger_id'])
		writetoblockchainsys()
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
		print''
		print ("---------- Press CTRL + c at any time to stop the Datalogger ----------")
		timestamp()
		if os.path.isfile("APIlansig.db"):
			url = ("http://"+comm_creds['envoy_ip']+"/api/v1/production")
			json_data = urltestandjsonload(url)
			total_energy = float(json_data['wattHoursLifetime'])/1000000
		elif os.path.isfile("APIwebsig.db"):
			url = ("http://goodwe-power.com/Mobile/GetMyPowerStationById?stationID="+comm_creds['system_id'])
			json_data = urltestandjsonload(url)
			total_energy = (float(json_data['etotal'][0:-3])) / 1000
		else:
			databasenamebroken()

		print("Inverter API call successful: Total Energy MWh: {:.6f}") .format(total_energy)
		energy_log = maintainenergylog()

		if energy_log['energy_list_length'] >= 9 and energy_log['energy_list'][-1] >= (energy_log['energy_list'][0] + energy_reporting_increment):
			send_amount = calculateamounttosend()
			writetoblockchaingen()
			print ("Waiting {:.0f} seconds (approx {:.2f} days)") .format(inverter_query_increment, (inverter_query_increment/86400))
			sleeptimer()		
		else:
			energy_left = (energy_reporting_increment - (energy_log['energy_list'][energy_log['energy_list_length']-1] - energy_log['energy_list'][0])) * 1000
			if energy_left <= 0:
				energy_left = 0
			logs_left = 9 - energy_log['energy_list_length']
			if logs_left <= 0:
				logs_left = 0
			print ("Waiting for {} more unique energy logs and/or {:.3f} kWh more energy, will check again in {:.0f} seconds (approx {:.2f} days)") .format(logs_left, energy_left, inverter_query_increment, (inverter_query_increment/86400))
			sleeptimer()

	except KeyboardInterrupt:
       		del solarcoin_passphrase
       		gc.collect()
		print ''
		print("Stopping Datalogger in 10 seconds")
		time.sleep(10)
		sys.exit()
