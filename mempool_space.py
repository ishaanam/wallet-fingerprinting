import json
import requests

class MempoolSpace:
    def __init__(self):
        pass

    def normalize_tx(self, tx):
        for tx_out in tx["vout"]:
            tx_out["value"] = tx_out["value"] / 100000000
        return tx

    def get_tx(self, txid):
        return self.normalize_tx(self.getdecodedtransaction(txid))

    def getbestblockhash(self):
        URL = "https://mempool.space/api/blocks/tip/hash"
        response = requests.request("GET", URL)

        return response.text

    def getblocktxs(self, block_hash):
        URL = f"https://mempool.space/api/block/{block_hash}/txids"
        response = requests.request("GET", URL)

        return json.loads(response.text)

    def getrawmempool(self):
        URL = "https://mempool.space/api/mempool/txids"
        response = requests.request("GET", URL)

        return response.text

    def getrawtransaction(self, txid):
        URL = f"https://mempool.space/api/tx/{txid}/hex"
        response = requests.request("GET", URL)

        return response.text

    def getdecodedtransaction(self, txid):
        URL = f"https://mempool.space/api/tx/{txid}"
        response = requests.request("GET", URL)

        return json.loads(response.text)

    def getblocks(self, start_height):
        URL = f"https://mempool.space/api/v1/blocks/{start_height}"
        response = requests.request("GET", URL)
        blocks = json.loads(response.text)
        
        return [block["id"] for block in blocks]

