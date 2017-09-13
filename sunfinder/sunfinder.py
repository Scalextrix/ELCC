#!/usr/bin/env python

"""sunfinder.py: Queries the Chainz SolarCoin Explorer API, pulls solar production data and 
loads to database"""


__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.0"

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
	c.execute('''CREATE TABLE IF NOT EXISTS SOLARDETAILS (id INTEGER PRIMARY KEY AUTOINCREMENT, txhash TEXT UNIQUE, block TEXT, time TEXT, dataloggerid BLOB, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT, period TEXT, totalmwh TEXT)''')
	conn.commit()
	conn.close()

def databaseupdate():
	conn = sqlite3.connect('solardetails.db')
        c = conn.cursor()
     	c.execute("INSERT OR IGNORE INTO SOLARDETAILS VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?);", (tx_hash, block, block_time, datalogger_id, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi, period, total_mwh,))
        conn.commit()
        conn.close()

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
		last_block = blocks[-1]
		counter_max = len(blocks)

                if last_block <= 1899000:
                        print 'Minimum safe blockheight of 1899000 reached: Exiting in 10 seconds'
			time.sleep(10)
			sys.exit()	
		else:
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
			counter = 0
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
					peak_watt = first_message_decoded['Size_kW']
					latitude = first_message_decoded['lat']
					longitude = first_message_decoded['long']
					message = first_message_decoded['Comment']
					rpi = first_message_decoded['IoT']
					period = first_message_decoded['period']
					databaseupdate()
					print ('In block: {}').format(block)
					print ('UserID: {}').format(datalogger_id)
					print ('made TX hash: {}').format(tx_hash)
					print ('and recorded a total of: {} MWh of energy').format(total_mwh)
					print''
				except:
					print ('Skipping load: Message in block {} does not conform').format(block)
					print''
				counter = counter+1
				if counter == counter_max:
					break

			conn = sqlite3.connect('solardetails.db')
			c = conn.cursor()
			row_count_end = c.execute('select count(*) FROM SOLARDETAILS').fetchone()[0]
			conn.close()
			rows_added = row_count_end - row_count_start
			print ('{} new results added to database').format(rows_added)
			print ('Any more blocks to load?: {}').format(more_blocks)
			if more_blocks != True:
				print 'Found all blocks, exiting in 10 seconds'
				time.sleep(10)
				sys.exit()
			else:	
				print 'Waiting 10 seconds so as not to spam API, hit CTRL + c to stop search'
				time.sleep(10)

	except KeyboardInterrupt:
		print 'Stopping Sunfinder in 10 seconds'
		time.sleep(10)
		sys.exit()
