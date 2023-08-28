import requests
import json
import bitcoin_core
import mempool_space

local = False

try:
    bitcoin_core.getbestblockhash()
    print("Using Bitcoin Core")
    local = True
except requests.exceptions.ConnectionError:
    # Use mempool.space instead
    mempool_space.getbestblockhash()
    print("Using mempool.space")
    module = mempool_space

def get_tx(txid):
    if local:
        return normalize_bc_tx(bitcoin_core.decoderawtransaction(bitcoin_core.getrawtransaction(txid)))
    else:
        return normalize_ms_tx(mempool_space.getdecodedtransaction(txid))

def getblocktxs(block_hash):
    if local:
        return bitcoin_core.getblock(block_hash)["tx"]
    else:
        return mempool_space.getblocktransactions(block_hash)

def getbestblockhash():
    if local:
        return bitcoin_core.getbestblockhash()
    else:
        return mempool_space.getbestblockhash()

def get_prev_txout(tx_in):
    prev_txout = bitcoin_core.decoderawtransaction(bitcoin_core.getrawtransaction(tx_in["txid"]))["vout"][tx_in["vout"]]
    return prev_txout

def normalize_ms_tx(tx):
    for tx_out in tx["vout"]:
        tx_out["value"] = tx_out["value"] / 100000000
    return tx

def normalize_bc_tx(tx):
    for tx_in in tx["vin"]:
        tx_in["scriptsig_asm"] = tx_in["scriptSig"]["asm"]
        tx_in["scriptsig"] = tx_in["scriptSig"]["hex"]
        del tx_in["scriptSig"]
        try:
            tx_in["witness"] = tx_in["txinwitness"]
            del tx_in["txinwitness"]
        except KeyError:
            pass
        tx_in["prevout"] = normalize_txout(get_prev_txout(tx_in))
    tx["vout"] = [normalize_txout(tx_out) for tx_out in tx["vout"]]
    return tx

def normalize_txout(txout):
    txout["scriptpubkey"] = txout["scriptPubKey"]["hex"]
    try:
        txout["scriptpubkey_address"] = txout["scriptPubKey"]["address"]
    except KeyError:
        pass
    txout["scriptpubkey_type"] = txout["scriptPubKey"]["type"]
    del txout["scriptPubKey"]
    return txout

def get_confirmation_height(txid):
    mempool_space = f"https://mempool.space/api/tx/{txid}/status"
    response = requests.request("GET", mempool_space)
    ret = json.loads(response.text)
    if not ret["confirmed"]:
        return -1
    return ret["block_height"]

if __name__ == '__main__':
    txid = "9f2a977dc06de412e3316ab26462225ef26474ccc58d3326f0ac97fb8e71c8bc"
    # tx = bitcoin_core.decoderawtransaction(bitcoin_core.getrawtransaction(txid))
    # print(mempool_space.getdecodedtransaction(txid))
    # print(tx)
    # print(normalize_bc_tx(tx))
