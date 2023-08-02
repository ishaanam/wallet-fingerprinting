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
    BIP69 = 4

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

# Returns false if there is an r value of more than 32 bytes
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

def get_change_index(tx):
    vout = tx["vout"]

    # if single, return -1 as index
    if len(vout) == 1:
        return -1

    input_types = get_spending_types(tx)
    output_types = get_sending_types(tx)

    # if all inputs are of the same type, and only one output of the outputs is of that type, 
    if (len(set(input_types)) == 1):
        if output_types.count(input_types[0]) == 1:
            return output_types.index(input_types[0])

    # same as one of the input addresses
    prev_txouts  = [get_prev_txout(tx_in) for tx_in in tx["vin"]]
    input_script_pub_keys = [tx_out["scriptPubKey"]["hex"] for tx_out in prev_txouts]
    output_script_pub_keys = [tx_out["scriptPubKey"]["hex"] for tx_out in vout]

    shared_address = list(set(output_script_pub_keys).intersection(set(input_script_pub_keys)))

    if len(shared_address) == 1 and output_script_pub_keys.count(shared_address[0]) == 1:
        return output_script_pub_keys.index(shared_address[0])

    # TODO: Unnecessary Input Heuristic: https://en.bitcoin.it/wiki/Privacy#Change_address_detection
    # input_amounts = [tx_out["value"] for tx_out in prev_txouts]
    # output_amounts = [tx_out["value"] for tx_out in vout]

    # TODO: Add check for round numbers (in satoshis and dollars)

    # else inconclusive, return -2
    return -2

def get_output_structure(tx):
    vout = tx["vout"]
    if len(vout) == 1:
        return [OutputStructureType.SINGLE]

    output_structure = []

    if len(vout) == 2:
        output_structure.append(OutputStructureType.DOUBLE)
    else:
        output_structure.append(OutputStructureType.MULTI)

    # The following outputs structure types are mutually exclusive

    # Change Index

    change_index = get_change_index(tx)

    if change_index == len(tx["vout"]) - 1:
        output_structure.append(OutputStructureType.CHANGE_LAST)

    # BIP 69
    amounts = []
    outputs = []

    for tx_out in vout:
        amounts.append(tx_out["value"])
        outputs.append(tx_out["scriptPubKey"]["hex"])

    # There are duplicate amounts, so we also have to compare
    # by scriptPubKey
    if set(amounts) != amounts:
        if sorted(outputs) == outputs and sorted(amounts) == amounts:
            output_structure.append(OutputStructureType.BIP69)
            return output_structure
    else:
        if sorted(amounts) == amounts:
            output_structure.append(OutputStructureType.BIP69)
            return output_structure

    return output_structure

def has_multi_type_vin():
    input_types = get_spending_types(tx)
    if len(set(input_types)) == 1:
        return True
    return False

# -1 if definitely not
# 0 if possible
# 1 if very likely
# Note: also add if there isn't OP_CLTV in one of the inputs
def is_anti_fee_sniping(tx):
    locktime = tx["locktime"]
    if locktime == 0:
        return -1
    tx_height = get_confirmation_height(tx["txid"])
    if tx_height - locktime >= 100:
        return 0
    return 1

def change_type_matched_inputs(tx):
    change_index = get_change_index(tx)
    if change_index < 0:
        return False
    change_type = tx["vout"][change_index]["type"]

    input_types = get_spending_types(tx)

    if change_type in input_types:
        return True
    return False

def sequence_value(tx):
    pass

# need historical mempool data for this to be completely accurate
def spends_unconfirmed(tx):
    pass
