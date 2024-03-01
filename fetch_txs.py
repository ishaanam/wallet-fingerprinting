import json

import requests

from bitcoin_core import BitcoinCore
from mempool_space import MempoolSpace
from type import TxId

# TODO: add a protocol for BitcoinCore and MempoolSpace
try:
    BitcoinCore.getbestblockhash()
    bitcoin_client = BitcoinCore
    print("Using Bitcoin Core")
except (requests.exceptions.ConnectionError, requests.exceptions.InvalidSchema):
    bitcoin_client = MempoolSpace
    print("Using mempool.space")


def get_confirmation_height(txid: TxId) -> int:
    mempool_space = f"https://mempool.space/api/tx/{txid}/status"
    response = requests.request("GET", mempool_space)
    ret = json.loads(response.text)
    if not ret["confirmed"]:
        return -1
    return ret["block_height"]
