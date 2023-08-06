import configparser
import json
import requests

Config = configparser.ConfigParser()
Config.read("rpc_config.ini")

URL = Config.get("RPC_INFO", "URL")
RPCUSER = Config.get("RPC_INFO", "RPCUSER")
RPCPASSWORD = Config.get("RPC_INFO", "RPCPASSWORD")

def getbestblockhash():
    payload = json.dumps({"method": "getbestblockhash", "params": []})
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}
    response = requests.request("POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD))

    return json.loads(response.text)["result"]

def getblock(block_hash):
    payload = json.dumps({"method": "getblock", "params": [block_hash]})
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}
    response = requests.request("POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD))

    return json.loads(response.text)["result"]

def getrawmempool():
    payload = json.dumps({"method": "getrawmempool", "params": []})
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}
    response = requests.request("POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD))

    return json.loads(response.text)["result"]

def getrawtransaction(txid):
    payload = json.dumps({"method": "getrawtransaction", "params": [txid]})
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}
    response = requests.request("POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD))

    return json.loads(response.text)["result"]

def decoderawtransaction(tx_hex):
    payload = json.dumps({"method": "decoderawtransaction", "params": [tx_hex]})
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}
    response = requests.request("POST", URL, data=payload, headers=headers, auth=(RPCUSER, RPCPASSWORD))

    return json.loads(response.text)["result"]
