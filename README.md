# ELCC

These files are curently in Python 2.7 and should work natively on Raspberry Pi 2/3 with Raspian-lite or Debian 

v1.1 will request the users wallet passphrase, unlock then put the wallet back to staking after the transaction is issued, the script assumes the wallet is encrypted and that the wallet is unlocked for staking before the script is initiated

For the original script to complete successfully your SolarCoin wallet must be FULLY unlocked, unlocked for staking is not sufficient

  To fully unlock from the terminal: solarcoind walletpassphrase {enter_your_passphrase} 9999999
  
  Always lock your wallet for security reasons after running the script: solarcoind walletlock
