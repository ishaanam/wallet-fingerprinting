import json

import requests

from bitcoin_core import BitcoinCore
from mempool_space import MempoolSpace
from type import TxId

BitcoinClient = BitcoinCore()

# should have a protocol for this
try:
    BitcoinClient.getbestblockhash()
    print("Using Bitcoin Core")
except (requests.exceptions.ConnectionError, requests.exceptions.InvalidSchema):
    BitcoinClient = MempoolSpace()
    print("Using mempool.space")


def get_confirmation_height(txid: TxId) -> int:
    mempool_space = f"https://mempool.space/api/tx/{txid}/status"
    response = requests.request("GET", mempool_space)
    ret = json.loads(response.text)
    if not ret["confirmed"]:
        return -1
    return ret["block_height"]
