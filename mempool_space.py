import json

import requests

from type import BlockId, TxId, TxNotNormalized


class MempoolSpace:
    @staticmethod
    def normalize_tx(tx: TxNotNormalized) -> TxNotNormalized:
        for tx_out in tx["vout"]:
            tx_out["value"] = tx_out["value"] / 100000000
        return tx

    @staticmethod
    def get_tx(txid: TxId) -> TxNotNormalized:
        return MempoolSpace.normalize_tx(MempoolSpace.getdecodedtransaction(txid))

    @staticmethod
    def getbestblockhash():
        URL = "https://mempool.space/api/blocks/tip/hash"
        response = requests.request("GET", URL)

        return response.text

    @staticmethod
    def getblocktxs(block_hash: BlockId) -> list[TxId]:
        URL = f"https://mempool.space/api/block/{block_hash}/txids"
        response = requests.request("GET", URL)

        return json.loads(response.text)

    def getrawmempool(self):
        URL = "https://mempool.space/api/mempool/txids"
        response = requests.request("GET", URL)

        return response.text

    @staticmethod
    def getrawtransaction(txid: TxId) -> str:
        URL = f"https://mempool.space/api/tx/{txid}/hex"
        response = requests.request("GET", URL)
        return response.text

    @staticmethod
    def getdecodedtransaction(txid: TxId) -> TxNotNormalized:
        URL = f"https://mempool.space/api/tx/{txid}"
        response = requests.request("GET", URL)
        return json.loads(response.text)

    @staticmethod
    def getblocks(start_height: int) -> list[BlockId]:
        URL = f"https://mempool.space/api/v1/blocks/{start_height}"
        response = requests.request("GET", URL)
        blocks = json.loads(response.text)
        return [block["id"] for block in blocks]
