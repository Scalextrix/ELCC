#!/usr/bin/env python

"""sunfinderlocal.py: Queries the SolarCoin Daemon, pulls solar production data and
loads to database"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "3.0"

from datetime import datetime
import hashlib
import json
import os.path
import sqlite3
import subprocess
import sys
import time

def checksum():
	hasher = hashlib.sha1()
	current_path = os.path.dirname(__file__)
	datalogger_path = os.path.abspath(os.path.join(current_path, "..", "Enphase", "datalogger.py"))
	with open(datalogger_path, 'rb') as afile:
		buf = afile.read()
		hasher.update(buf)
	return (hasher.hexdigest())

def databasecreate():
	conn = sqlite3.connect('solardetails.db')
	c = conn.cursor()
	c.execute('''CREATE TABLE IF NOT EXISTS GENDETAILS (unixdatetime INTEGER PRIMARY KEY, dataloggerid BLOB, txhash TEXT, block INTEGER, time TEXT, period TEXT, totalmwh REAL, incrementmwh REAL)''')
	c.execute('''CREATE TABLE IF NOT EXISTS SYSDETAILS (dataloggerid BLOB UNIQUE, panelid TEXT, inverterid TEXT, pkwatt TEXT, tilt TEXT, azimuth TEXT, lat TEXT, lon TEXT, msg TEXT, datalogger TEXT, slrsigaddr TEXT)''')
	c.execute('''CREATE TABLE IF NOT EXISTS BLOCKTRACK (block_number INTEGER UNIQUE, block_hash TEXT)''')
	conn.commit()
	conn.close()

def databaseupdategen():
	conn = sqlite3.connect('solardetails.db')
	c = conn.cursor()
	c.execute("INSERT OR IGNORE INTO GENDETAILS VALUES (?,?,?,?,?,?,?,?);", (enddatetime, datalogger_id, tx_hash, block_number, block_time, period, total_mwh, increment_mwh,))
	c.execute('INSERT OR REPLACE INTO BLOCKTRACK VALUES (?,?);', (block_number, block_hash,))	
	conn.commit()
	conn.close()

def databaseupdatesys():
	conn = sqlite3.connect('solardetails.db')
	c = conn.cursor()
	c.execute("INSERT OR IGNORE INTO SYSDETAILS VALUES (?,?,?,?,?,?,?,?,?,?,?);", (datalogger_id, solar_panel, solar_inverter, peak_watt, tilt, azimuth, latitude, longitude, message, datalogger, solarcoin_sig_address,))
	c.execute('INSERT OR REPLACE INTO BLOCKTRACK VALUES (?,?);', (block_number, block_hash,))
	conn.commit()
	conn.close()

def hashcheckergen():
	conn = sqlite3.connect('solardetails.db')
	c = conn.cursor()
	solarcoin_sig_address = str(c.execute("select slrsigaddr FROM SYSDETAILS where dataloggerid ='{}'".format(datalogger_id)).fetchone()[0])
	conn.close()
	checksum_tx_message = tx_message+checksum
        return subprocess.check_output(['solarcoind', 'verifymessage', solarcoin_sig_address, hash_present, checksum_tx_message], shell=False)

def forkfinder(start_block_number):
	# checks if the blockhash in the database matches the blockchain, if not recursively looks back 10 blocks until match found and restarts search
	chain_block_hash = str(subprocess.check_output(['solarcoind', 'getblockhash', str(start_block_number)], shell=False))
	conn = sqlite3.connect('solardetails.db')
	c = conn.cursor()
	dbase_block_hash = str(c.execute('select block_hash from BLOCKTRACK where block_number = {}'.format(start_block_number)).fetchone()[0])
	conn.close()
	if chain_block_hash == dbase_block_hash:
		return start_block_number
	else:
		start_block_number = start_block_number -10
		print '******** CHAIN FORK DETECTED, LOOKING BACK TO BLOCK {} AND ATTEMPTING RELOAD ********'.format(start_block_number)
		return forkfinder(start_block_number)

def hashcheckersys():
	checksum_tx_message = tx_message+checksum
	return subprocess.check_output(['solarcoind', 'verifymessage', solarcoin_sig_address, hash_present, checksum_tx_message], shell=False)

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
	return (utc_dt - datetime(1970, 1, 1)).total_seconds()

checksum = str(checksum())

while True:
	top_block = int(subprocess.check_output(['solarcoind', 'getblockcount'], shell=False))
	if os.path.isfile("solardetails.db"):
		conn = sqlite3.connect('solardetails.db')
		c = conn.cursor()
		start_block_number = int(c.execute('select max(block_number) from BLOCKTRACK').fetchone()[0])
		conn.commit()
		conn.close()
		start_block_number = forkfinder(start_block_number)
	else:
		start_block_number = raw_input('Start search at which block?: ')
		try:
			int(start_block_number)
		except:
			print 'You must enter a whole number, please try again'
			sys.exit()
	
	block_number = int(start_block_number)
	databasecreate()
	while True:
		block_hash = subprocess.check_output(['solarcoind', 'getblockhash', str(block_number)], shell=False)
		tx_details = subprocess.check_output(['solarcoind', 'getblock', (block_hash)], shell=False)
		block_json = json.loads(tx_details)
		block_time = block_json['time']
        	tx_length = len(block_json['tx'])
        	print 'Number of transactions in block {} = {}'.format(block_number, tx_length-1)
        	tx_counter = 1
		while True:
			tx_hash = block_json['tx'][tx_counter]
			transaction = subprocess.check_output(['solarcoind', 'getrawtransaction', str(tx_hash), '1'], shell=False)
			tx_json = json.loads(transaction)
			tx_message = str(tx_json['tx-comment'])
			hash_present = tx_message[tx_message.find('Sig:')+4:tx_message.find('=')+1]
			print 'Decoding Transaction {}'.format(tx_counter)
			if tx_message[5:10] == 'sysv1':
				try:
					tx_message = tx_message[tx_message.find('{'):tx_message.find('}')+1]
					tx_message_decoded = json.loads(tx_message)
					solarcoin_sig_address = tx_message_decoded['SigAddr']
					datalogger_id = tx_message_decoded['UID']
					solar_panel = tx_message_decoded['module']
					tilt = tx_message_decoded['tilt']
					azimuth = tx_message_decoded['azimuth']
					solar_inverter = tx_message_decoded['inverter']
					datalogger = tx_message_decoded['data-logger']
					peak_watt = tx_message_decoded['Size_kW']
					latitude = tx_message_decoded['lat']
					longitude = tx_message_decoded['long']
					message = tx_message_decoded['Comment']
					hash_check = hashcheckersys()
					if hash_check[0] == 't':
						databaseupdatesys()
						print''
						print ('In Block {} Added or Updated System Details for System: {}').format(block_number, datalogger_id)
					else:
						print''
						print ('In Block {} System Details Hash check failed, not loading to database').format(block_number)
				except:
					print ('Skipping load: Message in block {} does not conform').format(block_number)
				print''
                        	
			elif tx_message[5:10] == 'genv1':
				try:
					tx_message = tx_message[tx_message.find('{'):tx_message.find('}')+1]
					tx_message_decoded = json.loads(tx_message)
					datalogger_id = tx_message_decoded['UID']
					hash_check = hashcheckergen()
					increment_mwh = 0
					db_counter = 0
					while True:
						total_mwh = tx_message_decoded['MWh{}'.format(db_counter)]
						period = tx_message_decoded['t{}'.format(db_counter)]
						enddatetime = periodtounixtime()
						if hash_check[0] == 't':
							databaseupdategen()
						db_counter = db_counter + 1
						if db_counter == 8:
							break
					print ('In block: {}').format(block_number)
					print ('UserID: {}').format(datalogger_id)
					print ('made TX hash: {}').format(tx_hash)
					print ('and recorded a total of: {} MWh of energy').format(total_mwh)
					print ('Message hash check passed: {}').format(hash_check)
					print''
					incrementmwhs()
				except:
					print ('Skipping load: Message in block {} does not conform').format(block_number)
					print''                	

			else:
				print 'Nothing to load in that transaction'
				conn = sqlite3.connect('solardetails.db')
				c = conn.cursor()
				c.execute('INSERT OR REPLACE INTO BLOCKTRACK VALUES (?,?);', (block_number, block_hash,)) 
				conn.commit()
				conn.close()

			tx_counter = tx_counter + 1
			if tx_counter == tx_length:
				break
		block_number = block_number + 1
		if block_number == top_block:
			conn = sqlite3.connect('solardetails.db')
			c = conn.cursor()
			end_block_number = int(c.execute('select max(block_number) from BLOCKTRACK').fetchone()[0])
			conn.close()
			print 'Found {} new blocks'.format(end_block_number-start_block_number)
			break
	print 'Sleeping for 10 minutes, then looking for more blocks to eat!'
	time.sleep(600)

