# A Detailed Introduction to Wallet Fingerprinting

## What is a wallet fingerprint?

__Wallet Fingerprint__: An aspect/aspects of an on-chain Bitcoin transaction that can result in identifying the wallet which owns a given UTXO.
This can be done in two primary methods:

1. Identifying the owner by the receiving transaction. This entails primarily looking at the aspects of the output such as the `scriptPubKey`.
This is the easiest type of method to avoid being compromised by, since only the output is controlled by the receiver, and everything else
is controlled by the sender. All that really needs to be done here to prevent this is to not use any non-standard locking scripts. This has been
made particularly easy with the introduction of taproot, as now even threshold multisignature output scripts can look like single key output scripts.
It is also important to note that change identification is another method of doing this, but it relies on already knowing the wallet which is sending
the tx.

2. Identifying the owner by the spending transactions. This is the most commonly discussed type of wallet fingerprinting.

## What information is already available about wallet fingerprinting?

[include summaries here]
- https://github.com/achow101/wallet-fingerprinting/blob/main/fingerprints.md 
- https://github.com/achow101/wallet-fingerprinting
- https://b10c.me/observations/03-blockchaincom-recommendations/
- https://b10c.me/observations/01-locktime-stairs/

## A (mostly) Comprehensive List of Wallet Fingerprints

## Wallet Fingerprints by Wallet
