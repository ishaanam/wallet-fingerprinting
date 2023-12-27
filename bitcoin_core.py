import configparser
import json
import requests

Config = configparser.ConfigParser()
Config.read("rpc_config.ini")

URL = Config.get("RPC_INFO", "URL")
RPCUSER = Config.get("RPC_INFO", "RPCUSER")
RPCPASSWORD = Config.get("RPC_INFO", "RPCPASSWORD")

class BitcoinCore:
    def __init__(self):
        pass

    def get_prev_txout(self, tx_in):
        prev_txout = self.decoderawtransaction(self.getrawtransaction(tx_in["txid"]))["vout"][tx_in["vout"]]
        return prev_txout

    def normalize_tx(self, tx):
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

    def normalize_txout(self, txout):
        txout["scriptpubkey"] = txout["scriptPubKey"]["hex"]
        try:
            txout["scriptpubkey_address"] = txout["scriptPubKey"]["address"]
        except KeyError:
            pass
        txout["scriptpubkey_type"] = txout["scriptPubKey"]["type"]
        del txout["scriptPubKey"]
        return txout

    def get_tx(self, txid):
        return self.normalize_tx(self.decoderawtransaction(self.getrawtransaction(txid)))

    def getbestblockhash(self):
        payload = json.dumps({"method": "getbestblockhash", "params": []})
        headers = {'content-type': "application/json", 'cache-control': "no-cache"}
        response = requests.request("POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD))

        return json.loads(response.text)["result"]

    def getblocktxs(self, block_hash):
        payload = json.dumps({"method": "getblock", "params": [block_hash]})
        headers = {'content-type': "application/json", 'cache-control': "no-cache"}
        response = requests.request("POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD))

        return json.loads(response.text)["result"]["tx"]

    def getrawmempool(self):
        payload = json.dumps({"method": "getrawmempool", "params": []})
        headers = {'content-type': "application/json", 'cache-control': "no-cache"}
        response = requests.request("POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD))

        return json.loads(response.text)["result"]

    def getrawtransaction(self, txid):
        payload = json.dumps({"method": "getrawtransaction", "params": [txid]})
        headers = {'content-type': "application/json", 'cache-control': "no-cache"}
        response = requests.request("POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD))

        return json.loads(response.text)["result"]

    def decoderawtransaction(self, tx_hex):
        payload = json.dumps({"method": "decoderawtransaction", "params": [tx_hex]})
        headers = {'content-type': "application/json", 'cache-control': "no-cache"}
        response = requests.request("POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD))

        return json.loads(response.text)["result"]
