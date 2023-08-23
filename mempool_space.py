import json
import requests

def getbestblockhash():
    URL = "https://mempool.space/api/blocks/tip/hash"
    response = requests.request("GET", URL)

    response.text

def getblocktransactions(block_hash):
    URL = f"https://mempool.space/api/block/{block_hash}/txids"
    response = requests.request("GET", URL)

    return response.text

def getrawmempool():
    URL = "https://mempool.space/api/mempool/txids"
    response = requests.request("GET", URL)

    return response.text

def getrawtransaction(txid):
    URL = f"https://mempool.space/api/tx/{txid}/hex"
    response = requests.request("GET", URL)

    return response.text

def getdecodedtransaction(txid):
    URL = f"https://mempool.space/api/tx/{txid}"
    response = requests.request("GET", URL)

    return response.text
