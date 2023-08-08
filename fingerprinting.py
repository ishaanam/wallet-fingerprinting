from enum import Enum
from tqdm.notebook import tqdm

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

class Wallets(Enum):
    BITCOIN_CORE = 0
    ELECTRUM = 1
    BLUE_WALLET = 2
    COINBASE = 3
    EXODUS = 4
    TRUST = 5
    TREZOR = 6
    LEDGER = 7
    UNKNOWN = 8

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

def get_spending_types(tx, prev_txouts=None):
    types = []
    if not prev_txouts:
        prev_txouts  = [get_prev_txout(tx_in) for tx_in in tx["vin"]]
    for prev_txout in prev_txouts:
        types.append(prev_txout["scriptPubKey"]["type"])
    return types

def get_sending_types(tx):
    types = []
    for tx_out in tx["vout"]:
        types.append(tx_out["scriptPubKey"]["type"])
    return types

def compressed_public_keys_only(tx, prev_txouts=None):
    input_types = get_spending_types(tx, prev_txouts)
    for i, input_type in enumerate(input_types):
        if input_type == "witness_v0_keyhash":
            if tx["vin"][i]["txinwitness"][1][1] == '4':
                return False
        elif input_type == "pubkeyhash":
            if tx["vin"][i]["scriptSig"]["asm"][tx["vin"][i]["scriptSig"]["asm"].find(" ") + 2] == '4':
                return False
    return True

def get_input_order(tx, prev_txouts=None):
    if len(tx["vin"]) == 1:
        return [InputSortingType.SINGLE]
    sorting_types = []
    amounts = []
    prevouts = []

    if not prev_txouts:
        prev_txouts  = [get_prev_txout(tx_in) for tx_in in tx["vin"]]

    for i, tx_in in enumerate(tx["vin"]):
        prevouts.append(f"{tx_in['txid']}:{tx_in['vout']}")
        amounts.append(prev_txouts[i]["value"])

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
def low_r_only(tx, prev_txouts=None):
    input_types = get_spending_types(tx, prev_txouts)
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

def get_change_index(tx, prev_txouts=None):
    vout = tx["vout"]

    # if single, return -1 as index
    if len(vout) == 1:
        return -1

    input_types = get_spending_types(tx, prev_txouts)
    output_types = get_sending_types(tx)

    # if all inputs are of the same type, and only one output of the outputs is of that type, 
    if (len(set(input_types)) == 1):
        if output_types.count(input_types[0]) == 1:
            return output_types.index(input_types[0])

    # same as one of the input addresses
    if not prev_txouts:
        prev_txouts  = [get_prev_txout(tx_in) for tx_in in tx["vin"]]
    input_script_pub_keys = [tx_out["scriptPubKey"]["hex"] for tx_out in prev_txouts]
    output_script_pub_keys = [tx_out["scriptPubKey"]["hex"] for tx_out in vout]

    shared_address = list(set(output_script_pub_keys).intersection(set(input_script_pub_keys)))

    if len(shared_address) == 1 and output_script_pub_keys.count(shared_address[0]) == 1:
        return output_script_pub_keys.index(shared_address[0])

    # TODO: Unnecessary Input Heuristic: https://en.bitcoin.it/wiki/Privacy#Change_address_detection
    # input_amounts = [tx_out["value"] for tx_out in prev_txouts]

    output_amounts = [int(tx_out["value"] * 100000000) for tx_out in vout] # stored as satoshis

    possible_index = []

    for i, amount in enumerate(output_amounts):
        if amount % 100 != 0:
            possible_index.append(i)

    if len(possible_index) == 1:
        return possible_index[0]

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

def has_multi_type_vin(tx, prev_txouts=None):
    input_types = get_spending_types(tx, prev_txouts)
    if len(set(input_types)) == 1:
        return False
    return True

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

# 2 = no change / change inconclusive
# 1 = it matched inputs
# 0 = it matched neither/both inputs nor outputs
# -1 = it matched outputs
def change_type_matched_inputs(tx, prev_txouts=None):
    change_index = get_change_index(tx)
    if change_index < 0:
        return 2
    change_type = tx["vout"][change_index]["scriptPubKey"]["type"]

    input_types = get_spending_types(tx, prev_txouts)
    output_types = get_sending_types(tx)
    output_types.remove(change_type)

    if change_type in output_types:
        if change_type in input_types:
            return 0 # both
        return -1
    else:
        if change_type in input_types:
            return 1
        return 0 # neither

def address_reuse(tx, prev_txouts=None):
    if not prev_txouts:
        prev_txouts  = [get_prev_txout(tx_in) for tx_in in tx["vin"]]

    input_script_pub_keys = [tx_out["scriptPubKey"]["hex"] for tx_out in prev_txouts]
    output_script_pub_keys = [tx_out["scriptPubKey"]["hex"] for tx_out in tx["vout"]]

    shared_address = list(set(output_script_pub_keys).intersection(set(input_script_pub_keys)))
    if shared_address:
        return True
    return False

def signals_rbf(tx):
    for tx_in in tx["vin"]:
        if tx_in["sequence"] < 0xffffffff:
            return True
    return False

# need historical mempool data for this to be completely accurate
def spends_unconfirmed(tx):
    pass

def detect_wallet(tx):
    prev_txouts  = [get_prev_txout(tx_in) for tx_in in tx["vin"]]

    if not compressed_public_keys_only(tx, prev_txouts):
        return Wallets.UNKNOWN

    if tx["version"] == 1:
        if address_reuse(tx, prev_txouts):
            return Wallets.TRUST
        output_structure = get_output_structure(tx) 
        if OutputStructureType.MULTI in output_structure:
            return Wallets.TREZOR
        if output_structure != [OutputStructureType.SINGLE]:
            if OutputStructureType.BIP69 not in output_structure:
                return Wallets.LEDGER
        input_order = get_input_order(tx, prev_txouts)
        if input_order != [InputSortingType.SINGLE]:
            if InputSortingType.BIP69 not in input_order:
                return Wallets.LEDGER
            if InputSortingType.HISTORICAL not in input_order:
                return Wallets.TREZOR
        change_index = get_change_index(tx, prev_txouts)
        if change_index >= 0:
            if change_index != len(tx["vout"]) - 1: # if the last output was the change
                return Wallets.TREZOR
        spending_types = get_spending_types(tx, prev_txouts)
        if "witness_v1_taproot" in spending_types:
            return Wallets.TREZOR
    elif tx["version"] == 2:
        if is_anti_fee_sniping(tx) != -1:
            if low_r_only(tx, prev_txouts) and not address_reuse(tx, prev_txouts):
                output_structure = get_output_structure(tx) 
                if (output_structure != [OutputStructureType.SINGLE]) and (not OutputStructureType.BIP69 in output_structure):
                    return Wallets.BITCOIN_CORE
                input_ordering = get_input_order(tx, prev_txouts)
                if (input_ordering != [InputSortingType.SINGLE]) and (not InputSortingType.BIP69 in input_ordering):
                    return Wallets.BITCOIN_CORE
                if has_multi_type_vin(tx, prev_txouts):
                    return Wallets.BITCOIN_CORE
                spending_types = get_spending_types(tx, prev_txouts)
                if "witness_v1_taproot" in spending_types:
                    return Wallets.BITCOIN_CORE
                matching_change_type = change_type_matched_inputs(tx, prev_txouts)
                if matching_change_type == -1:
                    return Wallets.BITCOIN_CORE
                return Wallets.ELECTRUM
        else:
            if signals_rbf(tx):
                if has_multi_type_vin(tx, prev_txouts):
                    return Wallets.UNKNOWN
                spending_types = get_spending_types(tx, prev_txouts)
                if "witness_v0_keyhash" not in spending_types:
                    return Wallets.UNKNOWN
                change_index = get_change_index(tx, prev_txouts)
                if change_index >= 0 and change_index != len(tx["vout"]) - 1:
                    return Wallets.UNKNOWN
                return Wallets.BLUE_WALLET

            vout_len = len(tx["vout"])
            if vout_len > 2:
                return Wallets.UNKNOWN # doesn't signal RBF but has more than two outputs
            elif vout_len == 2:
                if address_reuse(tx, prev_txouts): # this is only address reuse between inputs and outputs (change same as input address)
                    return Wallets.EXODUS
                return Wallets.COINBASE
            elif vout_len == 1:
                sending_types = get_sending_types(tx)
                if "witness_v1_taproot" in sending_types:
                    return Wallets.EXODUS
                spending_types = get_spending_types(tx, prev_txouts)
                if "pubkeyhash" in spending_types:
                    return Wallets.COINBASE
    return Wallets.UNKNOWN

def get_tx(txid):
    return decoderawtransaction(getrawtransaction(txid))

def analyze_block(block_hash=None, num_of_txs=None):
    if not block_hash:
        block_hash = getbestblockhash()

    if num_of_txs:
        num_of_txs += 1

    # exclude the coinbase transaction
    transactions = getblock(block_hash)["tx"][1:num_of_txs]

    wallets = {}

    wallets[Wallets.BITCOIN_CORE] = 0
    wallets[Wallets.ELECTRUM] = 0
    wallets[Wallets.BLUE_WALLET] = 0
    wallets[Wallets.COINBASE] = 0
    wallets[Wallets.EXODUS] = 0
    wallets[Wallets.TRUST] = 0
    wallets[Wallets.TREZOR] = 0
    wallets[Wallets.LEDGER] = 0
    wallets[Wallets.UNKNOWN] = 0

    for txid in tqdm(transactions):
        wallets[detect_wallet(get_tx(txid))] += 1

    return wallets
