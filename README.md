# ELCC

This repository contains code that is intended to allow a user of a SolarCoin crypto-currency wallet (see www.solarcoin.org), to report solar PV generation data into the SolarCoin block-chain.  The ElectriCChain project (see www.electricchain.org) has published a standardized syntax for data reporting (https://github.com/lpninja/ELCCpv1) which is the foundation upon which future block-chain services can be built; the code here is compliant with this syntax.  The user will need access to information from their SolarCoin wallet and from their solar PV system to use the script successfully.

The first iterations are based on Enphase solar PV systems (see www.enphase.com  Powered by Enphase Energy).
The Enphase Enlighten system has a web API which can be used to pull the information from outside of the users LAN, this may be useful for owners of solar PV systems in multiple locations/on different LANs.  This version relies on an app that is published on https://developer.enphase.com/docs/quickstart.html, the user may use Scalextrix's app or may publish their own app and update the api_key in the Python script. 
NOTE: Scalextrix's web API is limited by the number/frequency of calls and is on the free Watt Plan https://developer.enphase.com/plans, if this becomes over subscribed, users will need to publish their own Enlighten app.

The Enphase Envoy system also has a LAN API that can be used when the data collection can be made from with in the solar PV operators LAN, this is the preferred method as it is is not centralized, has no usage/frequency tiers or charges.

It is intended that low power IoT devices will be used for running the block-chain and gathering the solar PV generation data.  These scripts are curently in Python 2.7 and should work natively on Raspberry Pi 2/3 with Raspian-lite or Debian. 

Version notes:

  v1.1 will request the users wallet passphrase, unlock then put the wallet back to staking after the transaction is issued, the  script assumes the wallet is encrypted and that the wallet is unlocked for staking before the script is initiated.

  For the original (no version) script to complete successfully your SolarCoin wallet must be FULLY unlocked, unlocked for staking is not sufficient
    To fully unlock from the terminal: solarcoind walletpassphrase {enter_your_passphrase} 9999999
    If you are holding large amounts of SolarCoin always lock your wallet for security reasons after running the script: solarcoind walletlock
