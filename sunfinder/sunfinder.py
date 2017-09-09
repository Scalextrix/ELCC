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
import re
import requests
import urllib2

api_key = "ab076d5d15c5"
url = ("https://chainz.cryptoid.info/slr/api.dws?q=txbymessage&key="+api_key+"&m=UserID")
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'}

print "Attempting Chainz API call and JSON data load"
json_data = str((requests.get(url, headers=headers)).content.decode())
json_decoded = json.loads(json_data)

for a in json_decoded:
	hashes = [a['hash'] for a in json_decoded]
	blocks = [a['height'] for a in json_decoded]
	time = [a['time'] for a in json_decoded]
	messages = [a['message'] for a in json_decoded]

counter = 0
while True:
	first_hash = hashes [counter]
	first_block = blocks [counter]
	first_message = str(messages [counter])
	first_message = first_message[first_message.find('{'):first_message.find('}')+1]
	first_message_decoded = json.loads(first_message)
	user_id = first_message_decoded['UserID']
	total_mwh = first_message_decoded['Total MWh']
	print ('In block: {}').format(first_block)
	print ('UserID: {}').format(user_id)
	print ('made TX hash: {}').format(first_hash)
	print ('and recorded: {} MWh of energy').format(total_mwh)
	print''
	counter = counter+1
	if counter == 20:
		break



