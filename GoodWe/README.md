GoodWe allows monitoring of inverters via an undocumented API, you will need your GoodWe System ID to access the data from your inverter.

Depending on the Python version, one package may need to be installed 'requests', on Linux:

    sudo apt-get install python-requests

To get the datalogger software:

    git clone https://github.com/Scalextrix/ELCC

    cd ELCC/GoodWe

    chmod +x datalogger.py
    
To start the datalogger:

    ./datalogger.py
