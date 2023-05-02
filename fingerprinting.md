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

## Why is the presence of a wallet fingerprint on a transaction a problem?
The primary reason this is a problem is because wallet fingerprinting can lead to address de-anonymization. Identifying the wallet used to create a transaction makes it easier to determine who created the transaction.
This could be a problem when you are doing a coinjoin, for example. If you use the same wallet for both your input and output your coinjoin could be rendered highly ineffective if you wallet has a known fingerprint.

## What information is already available about wallet fingerprinting?

- [achow101's list of wallet fingerprints](https://github.com/achow101/wallet-fingerprinting/blob/main/fingerprints.md)
- [0xb10c's blog post describing using blockchain.com's feerate recommendations as a wallet fingerprint](https://b10c.me/observations/03-blockchaincom-recommendations/)
- [Blockchair's documentation, which describes a small number of wallet fingerprints](https://blockchair.com/api/docs#link_M6)

## A (somewhat) Comprehensive List of Wallet Fingerprints

The following is a list of potential wallet fingerprints. It is important to note that this list does not take into account the feasability of actually detecting this fingerprint with a non-trivial accuracy rate.

- Change position in vout
    - the change could be identified by using some of [these](https://en.bitcoin.it/wiki/Privacy#Change_address_detection) heuristics.
- Change type
- The presence of dust
    - in the vin
    - in the vout
- Available Coins / Coin Selection [will expand]
    - spending negative EV inputs
    - this also includes what types of coins we consider "safe" to spend
- input types
    - support for certain oppcodes
- output types (other than change)
    - eg. does the change type match the rest of the outputs, or the input type
- input and output positions
    - whether or not [BIP 69](https://github.com/bitcoin/bips/blob/master/bip-0069.mediawiki) is followed
- nSequence [will expand]
    - opt-in rbf
    - full-rbf (would need mempool data to detect this)
- nLocktime [will expand]
    - anti-fee-sniping
- fees/feerates [will expand]
    - min/max allowed fees
    - following feerate reccomendations (see [this](https://b10c.me/observations/03-blockchaincom-recommendations/))
- max unconfirmed tx chain lengths (would need mempool data to detect this, unless ancestors were mined in the same block)
- low-r-grinding
- compressed/uncompressed ECDSA public keys (in non-segwit outputs)
- tx version
    - is the tx version set to 2 as a default, or only when needed?
- the presence of external inputs/allows collaborative transactions

## Utilizing Tx Clustering

Clustering: "the task of finding addresses that belongs to the same wallet as a given address" ([Jonas Nick's masters thesis](https://jonasnick.github.io/papers/thesis.pdf))

If no fingerprints can be found for a given transaction, clustering algorithms could be used to find other adresses belonging to the same wallet. This is helpful because then those transactions can be searched for fingerprints. Typically a de-anonymization techniques can be even more effective when multiple are used in tandem. 

## Assumptions Being Made
- default settings
- certain software versions
