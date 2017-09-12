The sunfinder script is designed to integrate with the SolarCoin Block Explorer at https://chainz.cryptoid.info/slr/
and extract solar PV generation data from the SolarCoin blockchain

# Dependencies

sunfinder.py is written for Python 2.7 and need the 'requests' module to be installed

> sudo apt-get install python-requests

You also need an API Key which can be requested from this page https://chainz.cryptoid.info/api.key.dws

sunviewer.py is also in Python 2.7 and needs 'numpy' and 'matplotlib' to be installed

> sudo apt-get install python-numpy

> sudo apt-get install python-matplotlib

Otherwise all modules are standard.  To use sunfinder.py/sunviewer.py

> git clone https://github.com/Scalextrix/ELCC

> cd ELCC/sunfinder

> chmod +x sunfinder.py

> chmod +x sunviewer.py

> ./sunfinder.py

When Sunfinder has found all data and is waiting, hit CTRL + c to stop it

> ./sunviewer.py

To run on a schedule add CRON jobs
