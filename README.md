# ELCC

This repository contains code that is intended to allow a user of a SolarCoin crypto-currency wallet (see www.solarcoin.org), to report solar PV generation data into the SolarCoin block-chain.  The ElectriCChain project (see www.electricchain.org) has published a standardized syntax for data reporting (https://github.com/lpninja/) which is the foundation upon which future block-chain services can be built; the code here is compliant with this syntax.  The user will need access to information from their SolarCoin wallet and from their solar PV system to use the script successfully.

The first iterations are based on Enphase solar PV systems (see www.enphase.com  Powered by Enphase Energy).
The Enphase Enlighten system has a web API which can be used to pull the information from outside of the users LAN, this may be useful for owners of solar PV systems in multiple locations/on different LANs.  This version relies on an app that is published on https://developer.enphase.com/docs/quickstart.html, the user may use Scalextrix's app or may publish their own app and update the api_key in the Python script. 
NOTE: Scalextrix's web API is limited by the number/frequency of calls and is on the free Watt Plan https://developer.enphase.com/plans, if this becomes over subscribed, users will need to publish their own Enlighten app.

The Enphase Envoy system also has a LAN API that can be used when the data collection can be made from with in the solar PV operators LAN, this is the preferred method as it is not centralized, has no usage/frequency tiers or charges.

It is intended that low power IoT devices will be used for running the block-chain and gathering the solar PV generation data.  These scripts are curently in Python 2.7 and should work natively on Raspberry Pi 2/3 with Raspian-lite or Debian, as designed to work with solarcoind only (not Qt).

Script will request the users wallet passphrase (passphrase is invisible while typed), unlock then put the wallet back to staking after the transaction is issued, the  script assumes the wallet is encrypted and that the wallet is either fully locked, or unlocked for staking before the script is initiated.

Example Transaction: https://chainz.cryptoid.info/slr/tx.dws?1110f4ab407c9bb7ba56b2e9a93284e7d2d5700d3fc0096675546eae00ddc63d.htm

Any tips to my SLR address: 8cESoZyjFvx2Deq6VjQLqPfAwu8UXjcBkK
