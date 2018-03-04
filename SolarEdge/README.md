Using this tool will source data from https://www.solaredge.com

The SolarEdge API allows users to source data for their system, this python script will then publish that data to the SolarCoin block-chain.

To use this program the user must know theie SolarEdge SiteID, and must also create an API key, details at: https://www.solaredge.com/sites/default/files/se_monitoring_api.pdf

The script is configured to remain within the maximim 300 API calls per day.

Depending on the Python version, one package may need to be installed 'requests', on Linux:
> sudo apt-get install python-requests

To get the datalogger software:
> git clone https://github.com/Scalextrix/ELCC

> cd ELCC/SolarEdge

> chmod +x datalogger.py

To start the datalogger:

> ./datalogger.py
