#!/usr/bin/env python

"""sunfinder.py: Queries the Chainz SolarCoin Explorer API, pulls solar production data and 
loads to database"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "2.0"

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
	c.execute('''CREATE TABLE IF NOT EXISTS SYSDETAILS (dataloggerid BLOB UNIQUE, panelid TEXT, inverterid TEXT, pkwatt TEXT, lat TEXT, lon TEXT, msg TEXT, pi TEXT, pyranometer TEXT, web_layer_api TEXT, datalogger TEXT)''')
	conn.commit()
	conn.close()

def gendatabaseupdate():
	conn = sqlite3.connect('solardetails.db')
        c = conn.cursor()
     	c.execute("INSERT OR IGNORE INTO GENDETAILS VALUES (?,?,?,?,?,?,?,?);", (enddatetime, datalogger_id, tx_hash, block, block_time, period, total_mwh, increment_mwh,))
        conn.commit()
        conn.close()

def sysdatabaseupdate():
	conn = sqlite3.connect('solardetails.db')
        c = conn.cursor()
     	c.execute("INSERT OR REPLACE INTO SYSDETAILS VALUES (?,?,?,?,?,?,?,?,?,?,?);", (datalogger_id, solar_panel, solar_inverter, peak_watt, latitude, longitude, message, rpi, pyranometer, web_layer_api, datalogger,))
        conn.commit()
        conn.close()

def incrementmwhs():
        # calculate an incremental MWh amount based on each users last Total MWh reading
	conn = sqlite3.connect('solardetails.db')
	c = conn.cursor()
	datalogger_id = c.execute('select DISTINCT dataloggerid FROM GENDETAILS').fetchall()
	datalogger_id = [str(f[0]) for f in datalogger_id]
	id_length = len(datalogger_id)
	counter1=0
	while True:
		while True:
			max_rows = [f[0] for f in (c.execute("select unixdatetime FROM GENDETAILS WHERE dataloggerid ='{}' AND incrementmwh=0".format(datalogger_id[counter1])).fetchall())]
			if len(max_rows) <= 1:
				break
			tot_energy0 = float(c.execute("select totalmwh FROM GENDETAILS where unixdatetime={}".format(max_rows[-2])).fetchone()[0])
			tot_energy1 = float(c.execute("select totalmwh FROM GENDETAILS where unixdatetime={}".format(max_rows[-1])).fetchone()[0])
			increment_mwh = float("{0:.6f}".format(tot_energy1 - tot_energy0))
			c.execute("update GENDETAILS SET incrementmwh = {} WHERE totalmwh = {}".format(increment_mwh, tot_energy1))
			conn.commit()
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

min_safe_block = 1916605 #The first block where tx-message conforms to standard and test data is not present
last_block = ""
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'}
api_key = apikeystore()
while True:
	try:
		print "Attempting Chainz API call and JSON data load"
		last_block = str(last_block)
		url = ("https://chainz.cryptoid.info/slr/api.dws?q=txbymessage&key="+api_key+"&m=UID&before="+last_block)
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
		conn.close()

		dbase_blocks = [int(a[0]) for a in dbase_blocks] 

		if first_block in dbase_blocks:
			print 'First block returned from API already in database, nothing new: Please try again later, stopping in 10 seconds'
			time.sleep(10)
			sys.exit()
		else:
			counter = 0
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
                                if first_message[5:10] == 'genv1':
                                        try:
                                                first_message = first_message[first_message.find('{'):first_message.find('}')+1]
                                                first_message_decoded = json.loads(first_message)
                                                datalogger_id = first_message_decoded['UID']
                                                increment_mwh = 0
                                                total_mwh = first_message_decoded['MWh0']
                                                period = first_message_decoded['t0']
                                                enddatetime = periodtounixtime()
                                                gendatabaseupdate()
                                                total_mwh = first_message_decoded['MWh1']
                                                period = first_message_decoded['t1']
                                                enddatetime = periodtounixtime()
                                                gendatabaseupdate()
                                                total_mwh = first_message_decoded['MWh2']
                                                period = first_message_decoded['t2']
                                                enddatetime = periodtounixtime()
                                                gendatabaseupdate()
                                                total_mwh = first_message_decoded['MWh3']
                                                period = first_message_decoded['t3']
                                                enddatetime = periodtounixtime()
                                                gendatabaseupdate()
                                                total_mwh = first_message_decoded['MWh4']
                                                period = first_message_decoded['t4']
                                                enddatetime = periodtounixtime()
                                                gendatabaseupdate()
                                                total_mwh = first_message_decoded['MWh5']
                                                period = first_message_decoded['t5']
                                                enddatetime = periodtounixtime()
                                                gendatabaseupdate()
                                                total_mwh = first_message_decoded['MWh6']
                                                period = first_message_decoded['t6']
                                                enddatetime = periodtounixtime()
                                                gendatabaseupdate()
                                                total_mwh = first_message_decoded['MWh7']
                                                period = first_message_decoded['t7']
                                                enddatetime = periodtounixtime()
                                                gendatabaseupdate()
                                                total_mwh = first_message_decoded['MWh8']
                                                period = first_message_decoded['t8']
                                                enddatetime = periodtounixtime()
                                                gendatabaseupdate()
                                                total_mwh = first_message_decoded['MWh9']
                                                period = first_message_decoded['t9']
                                                enddatetime = periodtounixtime()
                                                gendatabaseupdate()
				
                                                print ('In block: {}').format(block)
                                                print ('UserID: {}').format(datalogger_id)
                                                print ('made TX hash: {}').format(tx_hash)
                                                print ('and recorded a total of: {} MWh of energy').format(total_mwh)
                                                print''
                                        except:
                                                print ('Skipping load: Message in block {} does not conform').format(block)
                                                print''
                                        
                                elif first_message[5:10] == 'sysv1':
                                        try:
                                                first_message = first_message[first_message.find('{'):first_message.find('}')+1]
                                                first_message_decoded = json.loads(first_message)
                                                datalogger_id = first_message_decoded['UID']
                                                solar_panel = first_message_decoded['module']
                                                solar_inverter = first_message_decoded['inverter']
                                                datalogger = first_message_decoded['data-logger']
                                                pyranometer = first_message_decoded['pyranometer']
                                                web_layer_api = first_message_decoded['Web_layer_API']
                                                peak_watt = first_message_decoded['Size_kW']
                                                latitude = first_message_decoded['lat']
                                                longitude = first_message_decoded['long']
                                                message = first_message_decoded['Comment']
                                                rpi = first_message_decoded['IoT']
                                                sysdatabaseupdate()
                                                print ('Added or Updated System Details for System: {}').format(datalogger_id)
                                        except:
                                                print ('Skipping load: Message in block {} does not conform').format(block)
                                                print''

				counter = counter+1
				if counter == counter_max:
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
