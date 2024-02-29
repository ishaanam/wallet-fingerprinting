import configparser
import json
import warnings
from typing import cast, no_type_check

import requests

from type import (
    BlockHash,
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

URL = Config.get("RPC_INFO", "URL")
RPCUSER = Config.get("RPC_INFO", "RPCUSER")
RPCPASSWORD = Config.get("RPC_INFO", "RPCPASSWORD")


# #TODO: use @staticmethod
class BitcoinCore:
    def __init__(self):
        pass

    def get_prev_txout(self, tx_in: TxInNotNormalized) -> TxOutNotNormalized:
        prev_txout = self.decoderawtransaction(self.getrawtransaction(tx_in["txid"]))[
            "vout"
        ][tx_in["vout"]]
        return prev_txout

    @no_type_check
    def _untyped_normalize_tx(self, tx: TxNotNormalized) -> Tx:
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

    def _typed_normalize_tx(self, tx: TxNotNormalized) -> Tx:
        new_vin = list[TxInNormalized]()
        for tx_in in tx["vin"]:
            tx_in = cast(
                TxInNotNormalized, tx_in
            )  # pyright: ignore[reportUnnecessaryCast]

            new_in: TxInNormalized = {
                "txid": tx_in["txid"],
                # "vout": tx_in["vout"],
                "scriptsig_asm": tx_in["scriptSig"]["asm"],
                "scriptsig": tx_in["scriptSig"]["hex"],
                "witness": tx_in.get("txinwitness", []),
                "prevout": self.normalize_txout(self.get_prev_txout(tx_in)),
            }
            new_vin.append(new_in)
        new_vout = [self.normalize_txout(out) for out in tx["vout"]]
        return {"vin": new_vin, "vout": new_vout}

    def normalize_tx(self, tx: TxNotNormalized) -> Tx:
        try:
            return self._typed_normalize_tx(tx)
        except Exception as e:  # #TODO: remove
            warnings.warn(f"{e}")
            return self._untyped_normalize_tx(tx)  # type: ignore

    @no_type_check
    def _untyped_normalize_txout(self, txout):
        txout["scriptpubkey"] = txout["scriptPubKey"]["hex"]
        try:
            txout["scriptpubkey_address"] = txout["scriptPubKey"]["address"]
        except KeyError:
            pass
        txout["scriptpubkey_type"] = txout["scriptPubKey"]["type"]
        del txout["scriptPubKey"]
        return txout

    def normalize_txout(self, txout: TxOutNotNormalized) -> TxOutNormalized:
        try:
            return {
                "scriptpubkey": txout["scriptPubKey"]["hex"],
                "scriptpubkey_type": txout["scriptPubKey"]["type"],
                "scriptpubkey_address": txout["scriptPubKey"].get("address", None),
            }
        except Exception as e:  # #TODO: remove
            warnings.warn(f"{e}")
            return self._untyped_normalize_txout(txout)  # type: ignore

    def get_tx(self, txid: TxId):
        return self.normalize_tx(
            self.decoderawtransaction(self.getrawtransaction(txid))
        )

    def getbestblockhash(self):
        payload = json.dumps({"method": "getbestblockhash", "params": []})
        headers = {"content-type": "application/json", "cache-control": "no-cache"}
        response = requests.request(
            "POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD)
        )

        return json.loads(response.text)["result"]

    def getblocktxs(self, block_hash: BlockHash):
        payload = json.dumps({"method": "getblock", "params": [block_hash]})
        headers = {"content-type": "application/json", "cache-control": "no-cache"}
        response = requests.request(
            "POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD)
        )

        return json.loads(response.text)["result"]["tx"]

    def getrawmempool(self):
        payload = json.dumps({"method": "getrawmempool", "params": []})
        headers = {"content-type": "application/json", "cache-control": "no-cache"}
        response = requests.request(
            "POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD)
        )

        return json.loads(response.text)["result"]

    def getrawtransaction(self, txid: TxId):
        payload = json.dumps({"method": "getrawtransaction", "params": [txid]})
        headers = {"content-type": "application/json", "cache-control": "no-cache"}
        response = requests.request(
            "POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD)
        )

        return json.loads(response.text)["result"]

    def decoderawtransaction(self, tx_hex: TxHex):
        payload = json.dumps({"method": "decoderawtransaction", "params": [tx_hex]})
        headers = {"content-type": "application/json", "cache-control": "no-cache"}
        response = requests.request(
            "POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD)
        )

        return json.loads(response.text)["result"]
