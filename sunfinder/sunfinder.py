#!/usr/bin/env python

"""sunfinder.py: Queries the Chainz SolarCoin Explorer API, pulls solar production data and 
loads to database"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.0"

from datetime import datetime
import json
import os.path
import sqlite3
import sys
import time
import requests

def apikeystore():
	if os.path.isfile('APIkey.conf'):
		print 'Found stored API key in APIkey.conf'
		f = open('APIkey.conf', 'r')
		api_key = f.readline()
		f.close
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
	c.execute('''CREATE TABLE IF NOT EXISTS SOLARDETAILS (unixdatetime INTEGER PRIMARY KEY, txhash TEXT UNIQUE, block INTEGER, time TEXT, dataloggerid BLOB, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT, period TEXT, totalmwh REAL, incrementmwh REAL)''')
	conn.commit()
	conn.close()

def databaseupdate():
	conn = sqlite3.connect('solardetails.db')
        c = conn.cursor()
     	c.execute("INSERT OR IGNORE INTO SOLARDETAILS VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);", (enddatetime, tx_hash, block, block_time, datalogger_id, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi, period, total_mwh, increment_mwh,))
        conn.commit()
        conn.close()

def incrementmwhs():
	# calculate an incremental MWh amount based on each users last Total MWh reading	
	counter1=0
	counter2=row_count_start-2
	conn = sqlite3.connect('solardetails.db')
	c = conn.cursor()
	datalogger_id = c.execute('select DISTINCT dataloggerid FROM SOLARDETAILS').fetchall()
	datalogger_id = [str(f[0]) for f in datalogger_id]
	id_length = len(datalogger_id)
	while True:
		while True:
			max_rows = c.execute("select count(*) FROM SOLARDETAILS where dataloggerid ='{}'".format(datalogger_id[counter1])).fetchone()[0]
			if max_rows <= 1:
				break
			tot_energy0 = float(c.execute("select totalmwh FROM SOLARDETAILS where dataloggerid ='{}' limit {},1".format(datalogger_id[counter1], counter2)).fetchone()[0])
			counter2 = counter2+1
			tot_energy1 = float(c.execute("select totalmwh FROM SOLARDETAILS where dataloggerid ='{}' limit {},1".format(datalogger_id[counter1], counter2)).fetchone()[0])
			increment_mwh = float("{0:.6f}".format(tot_energy1 - tot_energy0))
			c.execute("update SOLARDETAILS SET incrementmwh = {} WHERE totalmwh = {}".format(increment_mwh, tot_energy1))
			print ('Updating Incremental Energy reading row {} for UserID {}').format(counter2, datalogger_id[counter1])
			conn.commit()
			if counter2 == max_rows -1:
				break
		counter1=counter1+1
		if counter1 == id_length:
			conn.close()
			print 'Incremental Energy Update Completed'
			break

def periodtounixtime():
	#take the end time from the 'period' parameter and convert to unix time for use as primary key
	timestamp = period[20:]
	utc_dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
	enddatetime = (utc_dt - datetime(1970, 1, 1)).total_seconds()
	return enddatetime

min_safe_block = 1899758 #The first block where tx-message conforms to standard
last_block = ""
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'}
api_key = apikeystore()
while True:
	try:
		print "Attempting Chainz API call and JSON data load"
		last_block = str(last_block)
		url = ("https://chainz.cryptoid.info/slr/api.dws?q=txbymessage&key="+api_key+"&m=UserID&before="+last_block)
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
		row_count_start = c.execute('select count(*) FROM SOLARDETAILS').fetchone()[0]
		dbase_blocks = c.execute('select block FROM SOLARDETAILS').fetchall()
		conn.close()

		dbase_blocks = [int(a[0]) for a in dbase_blocks] 

		if first_block in dbase_blocks:
			print 'First block returned from API already in database, nothing new: Please try again later, stopping in 10 seconds'
			time.sleep(10)
			sys.exit()
		else:
			counter = counter_max-1
			while True:
				try:
					tx_hash = hashes [counter]
					block = blocks [counter]
					block_time = block_t [counter]
					first_message = str(messages [counter])
					first_message = first_message[first_message.find('{'):first_message.find('}')+1]
					first_message_decoded = json.loads(first_message)
					datalogger_id = first_message_decoded['UserID']
					solar_panel = first_message_decoded['module']
					solar_inverter = first_message_decoded['inverter']
					datalogger = first_message_decoded['data-logger']
					pyranometer = first_message_decoded['pyranometer']
					windsensor = first_message_decoded['windsensor']
					rainsensor = first_message_decoded['rainsensor']
					waterflow = first_message_decoded['waterflow']
					web_layer_api = first_message_decoded['Web_layer_API']
					total_mwh = first_message_decoded['Total MWh']
					increment_mwh = 0
					peak_watt = first_message_decoded['Size_kW']
					latitude = first_message_decoded['lat']
					longitude = first_message_decoded['long']
					message = first_message_decoded['Comment']
					rpi = first_message_decoded['IoT']
					period = first_message_decoded['period']
					enddatetime = periodtounixtime()
					databaseupdate()
					print ('In block: {}').format(block)
					print ('UserID: {}').format(datalogger_id)
					print ('made TX hash: {}').format(tx_hash)
					print ('and recorded a total of: {} MWh of energy').format(total_mwh)
					print''
				except:
					print ('Skipping load: Message in block {} does not conform').format(block)
					print''

				counter = counter-1
				if counter == -1:
					break

			conn = sqlite3.connect('solardetails.db')
			c = conn.cursor()
			row_count_end = c.execute('select count(*) FROM SOLARDETAILS').fetchone()[0]
			lowest_dbase_block = c.execute('select min(block) FROM SOLARDETAILS').fetchone()[0]
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
