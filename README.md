# ElectriCChain: Solar PV Generation Monitoring

This repository contains code that is intended to allow a user of a SolarCoin crypto-currency wallet (see www.solarcoin.org), to report solar PV generation data into the SolarCoin block-chain.  The ElectriCChain project (see www.electricchain.org) has published a standardized syntax for data reporting (https://github.com/lpninja/) which is the foundation upon which future block-chain services can be built; the code here is compliant with this syntax.  The user will need access to information from their SolarCoin wallet and from their solar PV system to use the script successfully.

It is intended that low power IoT devices will be used for running the block-chain and gathering the solar PV generation data.  These scripts are curently in Python 2.7 and should work natively on Raspberry Pi 2/3 with Raspian-lite or Debian, it is designed to work with solarcoind only (not Qt).  Solarcoin repo available from https://github.com/onsightit/solarcoin

Instructions to compile SolarCoin daemon on Raspberry Pi: https://github.com/Scalextrix/SolarCoin-Raspberry-Pi-Node

See your inverter manufacturer directory for specific integrations.  The LED directory contains instructions for building a datalogger that can use a photosensitive cell to read pulses from a PV genertation meter, often fitted on systems that claim Feed in Tarriff.

Script asks for wallet passphrase (passphrase is invisible while typed), then asks for LAN or Web API (if available), it will unlock the wallet then put the wallet back to staking after the transaction is issued; the  script assumes the wallet is encrypted and that the wallet is either fully locked, or unlocked for staking before the script is initiated.

The Script will immediately send a Transaction to register the system information into the blockchain.  Therafter the solar inverter will be queried relative to the solar installation kWp (kilo-Watts peak) with large systems more frequently up to a maximum of 30 seconds, small systems as little as once every 20 days; the datalogger will collect incremental energy readings fromthe inverter, if the amount of energy collected equals or exceeds 10kWh since the last check then a sample of 10 x MWh readings will report to the block-chain; otherwise the solar inverter will be queried every x seconds until the total exceeds 10kWh.  Once the MWh of the system is reported to the block-chain, a new MWh checkpoint is set and the process re-starts querying every x seconds.

TIP: To run the datalogger in the background you can use:
> sudo apt-get update -y && sudo apt-get upgrade

> sudo apt-get install screen

Then to start a new screen:
> screen

To resume a screen:
> screen -r

To leave a screen session and leave it running CRTL+a then d.
To leave a screen session and kill it CTRL+a then k.

Example System Information Transaction: https://chainz.cryptoid.info/slr/tx.dws?a9f8bd0194d87e695fe32cc5b1f774d26dc844b60b5b90b09968dc66b13eb9a7.htm

Example Energy Generation Transaction: https://chainz.cryptoid.info/slr/tx.dws?d58161e19f11134f66870973c967d839ca9b2e573f75ed12a1af286a0f01ac40.htm

Any tips to my SLR address: 8cESoZyjFvx2Deq6VjQLqPfAwu8UXjcBkK  Thanks
