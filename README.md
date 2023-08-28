# Wallet Fingerprint Detector

This repository contains tools that can be used to identify wallet fingerprints in transactions, 
and then use those fingerprints to identify the wallet software that may have been used to create 
that transaction.

Note: none of the results produced by this code should be considered certain. It is possible that
a transaction was not created with one of the 8 wallets (Bitcoin Core, Electrum, Blue Wallet, Trezor, 
Ledger, Exodus, Trust Wallet, Coinbase Wallet) that this software is fammiliar with. It is also possible 
that one of the transactions provided exhibits the same exact fingerprints of one of these 8 wallets, but 
in reality a different wallet was used to create that transaction.

The notebook can be used [here on Google Colab](https://colab.research.google.com/drive/1hWVe9U-r5np_QiGNtM6qaapXq8YwQ1FX?usp=sharing), or it can be run locally (see below). These functions use Bitcoin Core or the mempool.space REST API to fetch information about the transactions. If Bitcoin Core is not configured, mempool.space will be used by default. The Google Colab notebook will always use mempool.space.

## Setting Up Bitcoin Core

You can connect to your Bitcoin node by configuring the RPC settings in `rpc_config.ini`.

## Setting Up Jupyter

In order to use the Jupyter notebook, you need to have Jupyter installed. This can be done by running
the following:

```
$ pip install jupyter
```

The notebook can be run by doing the following:

```
$ jupyter notebook
```

## Functions

`detect_wallet(txid)`: Given a transactions id, this function will attempt to determine 
the wallet that created it, and will provide information about the transaction.

`analyze_block(block_hash, num_of_txs)`: This function looks at the first specified number of transactions
in the specified block and breaks down the number of transactions likely created by the eight wallets
mentioned above. If `block_hash` isn't specified, by default the latest block is analyzed. If `num_of_txs`
is not specified, then all of the transactions in the block are analyzed (please not that this takes time).
