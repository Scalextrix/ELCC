www.enphase.com  Powered by Enphase Energy

The Enphase Enlighten system has a web API which can be used to pull the information from outside of the users LAN,
this may be useful for owners of solar PV systems in multiple locations/on different LANs.
This version relies on an app that is published on https://developer.enphase.com/docs/quickstart.html, 
the user may use Scalextrix's app or may publish their own app and update the api_key in the Python script. 

NOTE: Scalextrix's web API is limited by the number/frequency of calls and is on the free Watt Plan 
https://developer.enphase.com/plans, if this becomes over subscribed, users will need to publish their own Enlighten app.

The Enphase Envoy system also has a LAN API that can be used when the data collection can be made from within
the solar PV operators LAN, this is the preferred method as it is not centralized, has no usage/frequency tiers or charges.

There are two Python packages to be installed 'requests' and 'lxml'

> sudo apt-get install python-requests

> sudo apt-get install python-lxml


To start the datalogger:
> git clone https://github.com/Scalextrix/ELCC

> cd ELCC/Enphase

> chmod +x datalogger.py

> ./datalogger.py
