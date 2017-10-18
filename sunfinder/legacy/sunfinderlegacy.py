#!/usr/bin/env python

"""sunfinder.py: Queries the Chainz SolarCoin Explorer API, pulls solar production data and 
loads to database"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "2.0"

from datetime import datetime
import hashlib
import json
import os.path
import sqlite3
import subprocess
import sys
import time
import requests

def checksum():
	hasher = hashlib.sha1()
	current_path = os.path.dirname(__file__)
	datalogger_path = os.path.abspath(os.path.join(current_path, "..", "Enphase", "datalogger.py"))
	with open(datalogger_path, 'rb') as afile:  
		buf = afile.read()
		hasher.update(buf)
	checksum = (hasher.hexdigest())
	return checksum

def apikeystore():
	if os.path.isfile('APIkey.conf'):
		print 'Found stored API key in APIkey.conf'
		f = open('APIkey.conf', 'r')
		api_key = f.readline()
		f.close()
		return api_key
	else:
		api_key = raw_input('What is your Chainz API Key?: ')
		f = open('APIkey.conf', 'wb')
		f.write(api_key)
		f.close()
		return api_key	

def databasecreate():
	conn = sqlite3.connect('solardetails.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS GENDETAILS (unixdatetime INTEGER PRIMARY KEY, dataloggerid BLOB, txhash TEXT, block INTEGER, time TEXT, period TEXT, totalmwh REAL, incrementmwh REAL)''')
	c.execute('''CREATE TABLE IF NOT EXISTS SYSDETAILS (dataloggerid BLOB UNIQUE, panelid TEXT, inverterid TEXT, pkwatt TEXT, tilt TEXT, azimuth TEXT, lat TEXT, lon TEXT, msg TEXT, datalogger TEXT, slrsigaddr TEXT)''')
	conn.commit()
	conn.close()

def databaseupdategen():
	conn = sqlite3.connect('solardetails.db')
        c = conn.cursor()
     	c.execute("INSERT OR IGNORE INTO GENDETAILS VALUES (?,?,?,?,?,?,?,?);", (enddatetime, datalogger_id, tx_hash, block, block_time, period, total_mwh, increment_mwh,))
        conn.commit()
        conn.close()

def databaseupdatesys():
	conn = sqlite3.connect('solardetails.db')
        c = conn.cursor()
     	c.execute("INSERT OR IGNORE INTO SYSDETAILS VALUES (?,?,?,?,?,?,?,?,?,?,?);", (datalogger_id, solar_panel, solar_inverter, peak_watt, tilt, azimuth, latitude, longitude, message, datalogger, solarcoin_sig_address,))
        conn.commit()
        conn.close()

def hashcheckergen():
        conn = sqlite3.connect('solardetails.db')
        c = conn.cursor()
        solarcoin_sig_address = str(c.execute("select slrsigaddr FROM SYSDETAILS where dataloggerid ='{}'".format(datalogger_id)).fetchone()[0])
        conn.close()
        checksum_tx_message = first_message+checksum
        hash_check = subprocess.check_output(['solarcoind', 'verifymessage', solarcoin_sig_address, hash_present, checksum_tx_message], shell=False)
        return hash_check

def hashcheckersys():
        checksum_tx_message = first_message+checksum
        hash_check = subprocess.check_output(['solarcoind', 'verifymessage', solarcoin_sig_address, hash_present, checksum_tx_message], shell=False)
        return hash_check

def incrementmwhs():
        # calculate an incremental MWh amount based on each users last Total MWh reading
	conn = sqlite3.connect('solardetails.db')
	c = conn.cursor()
	datalogger_id = c.execute('select DISTINCT dataloggerid FROM GENDETAILS').fetchall()
	datalogger_id = [str(f[0]) for f in datalogger_id]
	id_length = len(datalogger_id)
	counter1=0
	while True:
		counter2=0
		while True:
			max_rows = c.execute("select count(*) FROM GENDETAILS where dataloggerid ='{}'".format(datalogger_id[counter1])).fetchone()[0]
			if max_rows <= 1:
				break
			tot_energy0 = float(c.execute("select totalmwh FROM GENDETAILS where dataloggerid ='{}' limit {},1".format(datalogger_id[counter1], counter2)).fetchone()[0])
			counter2 = counter2+1
			tot_energy1 = float(c.execute("select totalmwh FROM GENDETAILS where dataloggerid ='{}' limit {},1".format(datalogger_id[counter1], counter2)).fetchone()[0])
			increment_mwh = float("{0:.6f}".format(tot_energy1 - tot_energy0))
			c.execute("update GENDETAILS SET incrementmwh = {} WHERE totalmwh = {}".format(increment_mwh, tot_energy1))
			conn.commit()
			print ('Updating Incremental Energy reading row {} for UserID {}').format(counter2, datalogger_id[counter1])
			if counter2 == max_rows -1:
				break
		counter1=counter1+1
		if counter1 == id_length:
			conn.close()
			print 'Incremental Energy Update Completed'
			break

def periodtounixtime():
	#take the end time from the 'period' parameter and convert to unix time for use as primary key
	timestamp = period
	utc_dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
	enddatetime = (utc_dt - datetime(1970, 1, 1)).total_seconds()
	return enddatetime

min_safe_block = 0 #The first block where tx-message conforms to standard and test data is not present
last_block = ""
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'}
api_key = apikeystore()
checksum = str(checksum())

while True:
	try:
		print "Attempting Chainz API call and JSON data load"
		last_block = str(last_block)
		url = ("https://chainz.cryptoid.info/slr/api.dws?q=txbymessage&key="+api_key+"&m=text:sys&before="+last_block)
		json_data = str((requests.get(url, headers=headers)).content.decode())
		json_decoded = json.loads(json_data)

		before_block = json_decoded['before']
		more_blocks = json_decoded['more']

		for a in json_decoded:
			hashes = [a['hash'] for a in json_decoded['txs']]
			blocks = [a['height'] for a in json_decoded['txs']]
			block_t = [a['time'] for a in json_decoded['txs']]
			messages = [a['message'] for a in json_decoded['txs']]

		first_block = blocks[0]
		counter_max = len(blocks)
		last_block = blocks[counter_max-1]

		databasecreate()
		conn = sqlite3.connect('solardetails.db')
		c = conn.cursor()
		dbase_blocks = c.execute('select block FROM GENDETAILS').fetchall()
		conn.close()

		dbase_blocks = [int(a[0]) for a in dbase_blocks] 

		if first_block in dbase_blocks:
			print 'First Sytem Details Block returned from API already in database, nothing new: Now searching for Generation Details Blocks'
			break
		else:
			counter = 0
			while True:
                                tx_hash = hashes [counter]
                                block = blocks [counter]
				if block <= min_safe_block: #Temporary addition until 100+ results from min_safe_block
					print ('New results added to database')
					print ('Minimum safe blockheight of {} reached: Exiting in 10 seconds').format(min_safe_block)
					time.sleep(10)
					break
                		block_time = block_t [counter]
                        	first_message = str(messages [counter])
				hash_present = first_message[first_message.find('Sig:')+4:first_message.find('=')+1]
        
                                if first_message[5:10] == 'sysv1':
                                        try:
                                                first_message = first_message[first_message.find('{'):first_message.find('}')+1]
                                                first_message_decoded = json.loads(first_message)
						solarcoin_sig_address = first_message_decoded['SigAddr']
                                                datalogger_id = first_message_decoded['UID']
                                                solar_panel = first_message_decoded['module']
                                                tilt = first_message_decoded['tilt']
                                                azimuth = first_message_decoded['azimuth']
                                                solar_inverter = first_message_decoded['inverter']
                                                datalogger = first_message_decoded['data-logger']
                                                peak_watt = first_message_decoded['Size_kW']
                                                latitude = first_message_decoded['lat']
                                                longitude = first_message_decoded['long']
                                                message = first_message_decoded['Comment']
						hash_check = hashcheckersys()
                                                if hash_check[0] == 't':
							databaseupdatesys()
                                                	print''
                                                	print ('In Block {} Added or Updated System Details for System: {}').format(block, datalogger_id)
						else:
							print''
							print ('In Block {} System Details Hash check failed, not loading to database').format(block)
                                        except:
                                                print ('Skipping load: Message in block {} does not conform').format(block)
                                                print''

				counter = counter+1
				if counter == counter_max-1:
					break

			print ('Any more blocks to load?: {}').format(more_blocks)
			if more_blocks != True:   
				print 'Found all System Details Blocks, now searching for Generation Details Blocks'
                                break
			else:	
				print 'Waiting 10 seconds so as not to spam API, hit CTRL + c to stop search'
				time.sleep(10)
				
        except requests.exceptions.Timeout:
                print 'CONNECTION TIMEOUT: Try again later'
                time.sleep(10)
		sys.exit()

        except requests.exceptions.RequestException:
                print 'CONNECTION FAILED: Check Internet connection and API Key is correct'
                time.sleep(10)
		sys.exit()
		
	except KeyboardInterrupt:
		print 'Stopping Sunfinder in 10 seconds'
		time.sleep(10)
		sys.exit()

last_block = ""
while True:
	try:
		print "Attempting Chainz API call and JSON data load"
		last_block = str(last_block)
		url = ("https://chainz.cryptoid.info/slr/api.dws?q=txbymessage&key="+api_key+"&m=text:gen&before="+last_block)
		json_data = str((requests.get(url, headers=headers)).content.decode())
		json_decoded = json.loads(json_data)

		before_block = json_decoded['before']
		more_blocks = json_decoded['more']

		for a in json_decoded:
			hashes = [a['hash'] for a in json_decoded['txs']]
			blocks = [a['height'] for a in json_decoded['txs']]
			block_t = [a['time'] for a in json_decoded['txs']]
			messages = [a['message'] for a in json_decoded['txs']]

		first_block = blocks[0]
		counter_max = len(blocks)
		last_block = blocks[counter_max-1]

		databasecreate()
		conn = sqlite3.connect('solardetails.db')
		c = conn.cursor()
		row_count_start = c.execute('select count(*) FROM GENDETAILS').fetchone()[0]
		dbase_blocks = c.execute('select block FROM GENDETAILS').fetchall()
		gen_datalogger_id = c.execute('select dataloggerid FROM SYSDETAILS').fetchall()
		conn.close()

		dbase_blocks = [int(a[0]) for a in dbase_blocks]
		gen_datalogger_id = [str(a[0]) for a in gen_datalogger_id]

		if first_block in dbase_blocks:
			print 'First block returned from API already in database, nothing new: Please try again later, stopping in 10 seconds'
			time.sleep(10)
			sys.exit()
		else:
			counter = counter_max-1
			while True:
                                tx_hash = hashes [counter]
                                block = blocks [counter]
				if block <= min_safe_block: #Temporary addition until 100+ results from min_safe_block
					incrementmwhs()
					print ('New results added to database')
					print ('Minimum safe blockheight of {} reached: Exiting in 10 seconds').format(min_safe_block)
					time.sleep(10)
					sys.exit()
                		block_time = block_t [counter]
                        	first_message = str(messages [counter])
				hash_present = first_message[first_message.find('Sig:')+4:first_message.find('=')+1]
                                if first_message[5:10] == 'genv1':
                                        try:
                                                first_message = first_message[first_message.find('{'):first_message.find('}')+1]
                                                first_message_decoded = json.loads(first_message)
                                                datalogger_id = first_message_decoded['UID']
                                                if datalogger_id in gen_datalogger_id:
                                                        hash_check = hashcheckergen()
                                                        increment_mwh = 0
                                                        db_counter = 0
                                                        while True:
                                                                total_mwh = first_message_decoded['MWh{}'.format(db_counter)]
                                                                period = first_message_decoded['t{}'.format(db_counter)]
                                                                enddatetime = periodtounixtime()
                                                                if hash_check[0] == 't':
                                                                	databaseupdategen()
                                                                db_counter = db_counter + 1
                                                                if db_counter == 7:
                                                                        break
						print ('In block: {}').format(block)
                                                print ('UserID: {}').format(datalogger_id)
                                                print ('made TX hash: {}').format(tx_hash)
                                                print ('and recorded a total of: {} MWh of energy').format(total_mwh)
                                                print ('Message hash check passed: {}').format(hash_check)
                                                print''

                                        except:
                                                print ('Skipping load: Message in block {} does not conform').format(block)
                                                print''

				counter = counter-1
				if counter == -1:
					break

			conn = sqlite3.connect('solardetails.db')
			c = conn.cursor()
			row_count_end = c.execute('select count(*) FROM GENDETAILS').fetchone()[0]
			lowest_dbase_block = c.execute('select min(block) FROM GENDETAILS').fetchone()[0]
			conn.close()
			rows_added = row_count_end - row_count_start
			print ('{} new results added to database').format(rows_added)
			if lowest_dbase_block <= min_safe_block:
                                incrementmwhs()
				print ('Minimum safe blockheight of {} reached: Exiting in 10 seconds').format(min_safe_block)
				time.sleep(10)
				sys.exit()

			print ('Any more blocks to load?: {}').format(more_blocks)
			if more_blocks != True:
                                incrementmwhs()    
				print 'Found all blocks, exiting in 10 seconds'
				time.sleep(10)
				sys.exit()
			else:	
				print 'Waiting 10 seconds so as not to spam API, hit CTRL + c to stop search'
				time.sleep(10)
				
        except requests.exceptions.Timeout:
                print 'CONNECTION TIMEOUT: Try again later'
                time.sleep(10)
		sys.exit()

        except requests.exceptions.RequestException:
                print 'CONNECTION FAILED: Check Internet connection and API Key is correct'
                time.sleep(10)
		sys.exit()
		
	except KeyboardInterrupt:
		print 'Stopping Sunfinder in 10 seconds'
		time.sleep(10)
		sys.exit()
