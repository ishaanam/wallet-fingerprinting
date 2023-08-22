# Wallet Fingerprint Detector

This repository contains tools that can be used to identify wallet fingerprints in transactions, 
and then use those fingerprints to identify the wallet software that may have been used to create 
that transaction.

Note: none of the results produced by this code should be considered certain. It is possible that
a transaction was not created with one of the 8 wallets (Bitcoin Core, Electrum, Blue Wallet, Trezor, 
Ledger, Exodus, Trust Wallet, Coinbase Wallet) that this software is fammiliar with. It is also possible 
that one of the transactions provided exhibits the same exact fingerprints of one of these 8 wallets, but 
in reality a different wallet was used to create that transaction.

## Setup

In order to use this you must be running a Bitcoin Core node. You can connect to this node by
configuring the RPC settings in `rpc_config.ini`.

In order to use the Jupyter notebook, you need to have Jupyter installed. This can be done by running
the following:

```
$ pip install jupyter
```

The notebook can be run by doing the following:

```
$ jupyter notebook
```

