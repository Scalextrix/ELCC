The sunfinder script is designed to integrate with the SolarCoin Daemon
and extract solar PV generation data from the SolarCoin blockchain into a local SQLite database

# Dependencies

sunfinder.py is written for Python 2.7 and requires the machine to have RPC access to solarcoind (SolarCoin Daemon)

sunviewer.py is also in Python 2.7 and needs 'numpy' and 'matplotlib' to be installed

For Linux

> sudo apt-get install python-numpy

> sudo apt-get install python-matplotlib

> sudo apt-get install python-mpltoolkits.basemap

For Windows

> python -m pip install numpy

> python -m pip install matplotlib

Download the latest Basemap version for your platform from https://sourceforge.net/projects/matplotlib/files/matplotlib-toolkits/ and install as normal

Otherwise all modules are standard.  To use sunfinder.py/sunviewer.py

> git clone https://github.com/Scalextrix/ELCC

> cd ELCC/sunfinder

> chmod +x sunfinder.py

> chmod +x sunviewer.py

> ./sunfinder.py

When Sunfinder has found all data and is waiting, hit CTRL + c to stop it

> ./sunviewer.py

To run on a schedule add CRON jobs
