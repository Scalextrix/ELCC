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
row_count_end = c.execute('select count(*) FROM SOLARDETAILS').fetchone()[0]
energyplot = c.execute('select totalmwh FROM SOLARDETAILS').fetchall()
conn.close()
rows_added = row_count_end - row_count_start
print ('{} new results added to database').format(rows_added)
plt.plot(energyplot)
plt.xlim(row_count_end, 0)
plt.ylabel('Energy MWh')
plt.xlabel('Time')
plt.show()

