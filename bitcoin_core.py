import configparser
import json
import warnings
from typing import cast, no_type_check

import requests

from type import (
    BlockId,
    Tx,
    TxHex,
    TxId,
    TxInNormalized,
    TxInNotNormalized,
    TxNotNormalized,
    TxOutNormalized,
    TxOutNotNormalized,
)

Config = configparser.ConfigParser()
Config.read("rpc_config.ini")
header = {"content-type": "application/json", "cache-control": "no-cache"}

URL = Config.get("RPC_INFO", "URL")
RPCUSER = Config.get("RPC_INFO", "RPCUSER")
RPCPASSWORD = Config.get("RPC_INFO", "RPCPASSWORD")


class BitcoinCore:
    @staticmethod
    def get_prev_txout(tx_in: TxInNotNormalized) -> TxOutNotNormalized:
        prev_txout = BitcoinCore.decoderawtransaction(
            BitcoinCore.getrawtransaction(tx_in["txid"])
        )["vout"][tx_in["vout"]]
        return prev_txout

    @no_type_check
    @staticmethod
    def _untyped_normalize_tx(tx: TxNotNormalized) -> Tx:
        for tx_in in tx["vin"]:
            tx_in["scriptsig_asm"] = tx_in["scriptSig"]["asm"]
            tx_in["scriptsig"] = tx_in["scriptSig"]["hex"]
            del tx_in["scriptSig"]
            try:
                tx_in["witness"] = tx_in["txinwitness"]
                del tx_in["txinwitness"]
            except KeyError:
                pass
            tx_in["prevout"] = self.normalize_txout(self.get_prev_txout(tx_in))
        tx["vout"] = [self.normalize_txout(tx_out) for tx_out in tx["vout"]]
        return tx

    @staticmethod
    def _typed_normalize_tx(tx: TxNotNormalized) -> Tx:
        # #fix: copy all keys from TxNotNormalized to Tx, check if there are any
        # keys left in TxNotNormalized
        new_vin = list[TxInNormalized]()
        for tx_in in tx["vin"]:
            tx_in = cast(
                TxInNotNormalized, tx_in
            )  # pyright: ignore[reportUnnecessaryCast]

            new_in: TxInNormalized = {
                "txid": tx_in["txid"],
                "locktime": tx_in["locktime"],
                # locktime # not sure if needed
                "vout": tx_in["vout"],  # should not be read # type: ignore
                # #fix: `vout` in the old impl was not normalized like this
                "scriptsig_asm": tx_in["scriptSig"]["asm"],
                "scriptsig": tx_in["scriptSig"]["hex"],
                "witness": tx_in.get("txinwitness", []),
                "prevout": BitcoinCore.normalize_txout(
                    BitcoinCore.get_prev_txout(tx_in)
                ),
                "sequence": tx_in["sequence"],
            }
            new_vin.append(new_in)
        new_vout = [BitcoinCore.normalize_txout(out) for out in tx["vout"]]
        return {
            "vin": new_vin,
            "vout": new_vout,
            "locktime": tx["locktime"],
            "version": tx["version"],
            "txid": tx["txid"],
        }

    @staticmethod
    def normalize_tx(tx: TxNotNormalized) -> Tx:
        try:
            return BitcoinCore._typed_normalize_tx(tx)
        except Exception as e:  # #TODO: remove
            warnings.warn(f"{e}")
            return BitcoinCore._untyped_normalize_tx(tx)  # type: ignore

    @no_type_check
    @staticmethod
    def _untyped_normalize_txout(txout):
        txout["scriptpubkey"] = txout["scriptPubKey"]["hex"]
        try:
            txout["scriptpubkey_address"] = txout["scriptPubKey"]["address"]
        except KeyError:
            pass
        txout["scriptpubkey_type"] = txout["scriptPubKey"]["type"]
        del txout["scriptPubKey"]
        return txout

    @staticmethod
    def normalize_txout(txout: TxOutNotNormalized) -> TxOutNormalized:
        try:
            return {
                "scriptpubkey": txout["scriptPubKey"]["hex"],
                "scriptpubkey_type": txout["scriptPubKey"]["type"],
                "scriptpubkey_address": txout["scriptPubKey"].get("address", None),
                "value": txout["value"],
            }
        except Exception as e:  # #TODO: remove
            warnings.warn(f"{e}")
            return BitcoinCore._untyped_normalize_txout(txout)  # type: ignore

    @staticmethod
    def get_tx(txid: TxId) -> Tx:
        return BitcoinCore.normalize_tx(
            BitcoinCore.decoderawtransaction(BitcoinCore.getrawtransaction(txid))
        )

    @staticmethod
    def getbestblockhash() -> BlockId:
        payload = json.dumps({"method": "getbestblockhash", "params": []})
        response = requests.request(
            "POST", URL, data=payload, headers=header, auth=(RPCUSER, RPCPASSWORD)
        )

        return json.loads(response.text)["result"]

    @staticmethod
    def getblocktxs(block_hash: BlockId) -> list[TxId]:
        payload = json.dumps({"method": "getblock", "params": [block_hash]})
        response = requests.request(
            "POST", URL, data=payload, headers=header, auth=(RPCUSER, RPCPASSWORD)
        )

        return json.loads(response.text)["result"]["tx"]

    @staticmethod
    def getrawmempool():
        payload = json.dumps({"method": "getrawmempool", "params": []})
        response = requests.request(
            "POST", URL, data=payload, headers=header, auth=(RPCUSER, RPCPASSWORD)
        )

        return json.loads(response.text)["result"]

    @staticmethod
    def getrawtransaction(txid: TxId):
        payload = json.dumps({"method": "getrawtransaction", "params": [txid]})
        response = requests.request(
            "POST", URL, data=payload, headers=header, auth=(RPCUSER, RPCPASSWORD)
        )

        return json.loads(response.text)["result"]

    @staticmethod
    def decoderawtransaction(tx_hex: TxHex):
        payload = json.dumps({"method": "decoderawtransaction", "params": [tx_hex]})
        response = requests.request(
            "POST", URL, data=payload, headers=header, auth=(RPCUSER, RPCPASSWORD)
        )

        return json.loads(response.text)["result"]
