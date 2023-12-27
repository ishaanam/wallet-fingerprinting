import requests
import json
from bitcoin_core import BitcoinCore
from mempool_space import MempoolSpace


module = BitcoinCore()

try:
    module.getbestblockhash()
    print("Using Bitcoin Core")
except (requests.exceptions.ConnectionError, requests.exceptions.InvalidSchema):
    module = MempoolSpace()
    print("Using mempool.space")

def get_confirmation_height(txid):
    mempool_space = f"https://mempool.space/api/tx/{txid}/status"
    response = requests.request("GET", mempool_space)
    ret = json.loads(response.text)
    if not ret["confirmed"]:
        return -1
    return ret["block_height"]
