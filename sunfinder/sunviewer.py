#!/usr/bin/env python

"""sunviewer.py: Draws a basic chart based on sunfinder.py"""


__author__ = "Steven Campbell AKA Scalextrix"
__copyright__ = "Copyright 2017, Steven Campbell"
__license__ = "The Unlicense"
__version__ = "1.0"

import numpy as np
import matplotlib.pyplot as plt
import sqlite3

conn = sqlite3.connect('solardetails.db')
c = conn.cursor()
energyplot = c.execute('select totalmwh FROM SOLARDETAILS').fetchall()
blocknumber = c.execute('select block FROM SOLARDETAILS').fetchall()
unixtime = c.execute('select time FROM SOLARDETAILS').fetchall()
datetime = c.execute('select period FROM SOLARDETAILS').fetchall()
row_count_end = c.execute('select count(*) FROM SOLARDETAILS').fetchone()[0]
conn.close()
plt.plot(blocknumber, energyplot)
plt.ylabel('Total Energy MWh')
plt.xlabel('SolarCoin Blocks')
plt.show()

