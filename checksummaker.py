#!/usr/bin/env python

"""checksummaker.py: Creates SHA1 checksums of datalogger.py versions and adds to goodchecksums.txt, sunfinder.py
uses goodchecksums.txt to validate signatiures including checksums"""

__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2018, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.0"

import hashlib
import os.path

manufacturer = ["Enphase", "GoodWe", "SolarEdge"]

def checksum():
	hasher = hashlib.sha1()
	with open('{}/datalogger.py'.format(manufacturer[counter]), 'rb') as afile:
		buf = afile.read()
		hasher.update(buf)
	return (hasher.hexdigest())

f = open("sunfinder/goodchecksums.txt","a+")
hashlist = f.read().splitlines()

counter = 0
while True:
	if checksum() not in hashlist:
		f.write(checksum()+'\n')
	counter = counter+1
	if counter == len(manufacturer):
		f.close()
		break
