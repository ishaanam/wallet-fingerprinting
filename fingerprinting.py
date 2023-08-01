from enum import Enum

from bitcoin_core import *

class InputSortingType(Enum):
    SINGLE = 0
    ASCENDING = 1
    DESCENDING = 2
    BIP69 = 3
    HISTORICAL = 4
    UNKNOWN = 5

class OutputStructureType(Enum):
    SINGLE = 0
    DOUBLE = 1
    MULTI = 2
    CHANGE_LAST = 3
    CHANGE_FIRST = 4
    BIP69 = 5

def get_prev_txout(tx_in):
    prev_txout = decoderawtransaction(getrawtransaction(tx_in["txid"]))["vout"][tx_in["vout"]]
    return prev_txout

def get_confirmation_height(txid):
    mempool_space = f"https://mempool.space/api/tx/{txid}/status"
    response = requests.request("GET", mempool_space)
    ret = json.loads(response.text)
    if not ret["confirmed"]:
        return -1
    return ret["block_height"]

def get_spending_types(tx):
    types = []
    for tx_in in tx["vin"]:
        prev_txout = get_prev_txout(tx_in)
        types.append(prev_txout["scriptPubKey"]["type"])
    return types

def get_sending_types(tx):
    types = []
    for tx_out in tx["vout"]:
        types.append(tx_out["scriptPubKey"]["type"])
    return types

def has_more_than_2_outputs(tx):
    return len(tx["vout"]) > 2

def compressed_public_keys_only(tx):
    input_types = get_spending_types(tx)
    for i, input_type in enumerate(input_types):
        if input_type == "witness_v0_keyhash":
            if tx["vin"][i]["txinwitness"][1][1] == '4':
                return False
        elif input_type == "pubkeyhash":
            if tx["vin"][i]["scriptSig"]["asm"][tx["vin"][i]["scriptSig"]["asm"].find(" ") + 2] == '4':
                return False
    return True

def get_input_order(tx):
    if len(tx["vin"]) == 1:
        return [InputSortingType.SINGLE]
    sorting_types = []
    amounts = []
    prevouts = []

    for tx_in in tx["vin"]:
        prevouts.append(f"{tx_in['txid']}:{tx_in['vout']}")
        prev_txout = get_prev_txout(tx_in)
        amounts.append(prev_txout["value"])

    if sorted(amounts) == amounts:
        sorting_types.append(InputSortingType.ASCENDING)
    if sorted(amounts)[::-1] == amounts:
        sorting_types.append(InputSortingType.DESCENDING)

    if sorted(prevouts) == prevouts:
        sorting_types.append(InputSortingType.BIP69)

    prevout_conf_heights = {prevout: None for prevout in prevouts}

    for prevout in prevouts:
        txid = prevout[0:prevout.find(":")]
        conf_height = get_confirmation_height(txid)
        if conf_height != -1:
            prevout_conf_heights[prevout] = conf_height
        else:
            prevout_conf_heights.remove(prevout)

    ordered_conf_heights = list(prevout_conf_heights.values())

    if ordered_conf_heights == sorted(ordered_conf_heights):
        sorting_types.append(InputSortingType.HISTORICAL)

    if len(sorting_types) == 0:
        sorting_types.append(InputSortingType.UNKNOWN)
    return sorting_types

# Returns false if there is an r value of greater than 32 bytes
def low_r_only(tx):
    input_types = get_spending_types(tx)
    for i, input_type in enumerate(input_types):
        if input_type == "witness_v0_keyhash":
            r_len = tx["vin"][i]["txinwitness"][0][6:8]
            if int(r_len, 16) > 32:
                return False
        elif input_type == "pubkeyhash":
            r_len = tx["vin"][i]["scriptSig"]["asm"][6:8]
            if int(r_len, 16) > 32:
                return False
    return True

def sequence_value(tx):
    pass

def get_output_order(tx):
    pass

def get_change_index(tx):
    pass

def change_type_matched_inputs(tx):
    pass

def spends_unconfirmed(tx):
    pass

def is_anti_fee_sniping(tx):
    pass

