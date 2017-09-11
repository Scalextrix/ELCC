#!/usr/bin/env python

"""sunfinder.py: Queries the Chainz SolarCoin Explorer API, pulls solar production data and 
loads to database"""


__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.0"

import json
import sqlite3
import sys
import time
import requests

api_key = "ab076d5d15c5"
last_block = ""
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'}

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

		last_block = blocks[-1]

                if last_block <= 1700000:
                        print 'Minimum safe blockheight of 1700000 reached: Waiting 1 day for more results, hit CTRL + c to stop'
			time.sleep(86400)	
		else:
			databasecreate()
	        	conn = sqlite3.connect('solardetails.db')
                	c = conn.cursor()
                	row_count_start = c.execute('select count(*) FROM SOLARDETAILS').fetchone()[0]
                	conn.close()

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
					total_mwh = first_message_decoded['Total MWh']
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
				if counter == 100:
					break

			conn = sqlite3.connect('solardetails.db')
			c = conn.cursor()
			row_count_end = c.execute('select count(*) FROM SOLARDETAILS').fetchone()[0]
			conn.close()
			rows_added = row_count_end - row_count_start
			print ('{} new results added to database').format(rows_added)
			print ('Any more blocks to load?: {}').format(more_blocks)
			if more_blocks != True:
				print 'Waiting 1 day for more results, or hit CTRL + c to stop'
				time.sleep(86400)
			else:
				time.sleep(10)

	except KeyboardInterrupt:
		print 'Stopping Sunfinder in 10 seconds'
		time.sleep(10)
		sys.exit()
