# ELCC

This repository contains code that is intended to allow a user of a SolarCoin crypto-currenty wallet (see www.solarcoin.org), to report solar PV generation data into the SolarCoin block-chain.  The ElectriCChain project (see www.electricchain.org) has published a standardized syntax for data reporting (https://github.com/lpninja/ELCCpv1) which is the foundation upon which future block-chain services can be built; the code here is compliant with this syntax.
It is intended that low power IoT devices will be used for running the block-chain and gathering the solar PV generation data.  These files are curently in Python 2.7 and should work natively on Raspberry Pi 2/3 with Raspian-lite or Debian. 


Version notes:

  v1.1 will request the users wallet passphrase, unlock then put the wallet back to staking after the transaction is issued, the  script assumes the wallet is encrypted and that the wallet is unlocked for staking before the script is initiated

  For the original (no version) script to complete successfully your SolarCoin wallet must be FULLY unlocked, unlocked for staking is not sufficient
    To fully unlock from the terminal: solarcoind walletpassphrase {enter_your_passphrase} 9999999
    If you are holding large amounts of SolarCoin always lock your wallet for security reasons after running the script: solarcoind walletlock
