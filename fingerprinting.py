from enum import Enum
from tqdm.auto import tqdm

from fetch_txs import module, get_confirmation_height

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
    BITCOIN_CORE = "Bitcoin Core"
    ELECTRUM = "Electrum"
    BLUE_WALLET = "Blue Wallet"
    COINBASE = "Coinbase Wallet"
    EXODUS = "Exodus Wallet"
    TRUST = "Trust Wallet"
    TREZOR = "Trezor"
    LEDGER = "Ledger"
    UNCLEAR = "Unclear"
    OTHER = "Other"

def get_spending_types(tx):
    types = []
    for tx_in in tx["vin"]:
        types.append(tx_in["prevout"]["scriptpubkey_type"])
    return types

def get_sending_types(tx):
    types = []
    for tx_out in tx["vout"]:
        types.append(tx_out["scriptpubkey_type"])
    return types

def compressed_public_keys_only(tx):
    input_types = get_spending_types(tx)
    for i, input_type in enumerate(input_types):
        if input_type == "witness_v0_keyhash" or input_type == "v0_p2wpkh":
            if tx["vin"][i]["witness"][1][1] == '4':
                return False
        elif input_type == "pubkeyhash" or input_type == "p2pkh":
            if tx["vin"][i]["scriptsig_asm"][tx["vin"][i]["scriptsig_asm"].find(" ") + 2] == '4':
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
        amounts.append(tx_in["prevout"]["value"])

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
            del prevout_conf_heights[prevout]

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
            r_len = tx["vin"][i]["witness"][0][6:8]
            if int(r_len, 16) > 32:
                return False
        elif input_type == "pubkeyhash":
            r_len = tx["vin"][i]["scriptsig_asm"][6:8]
            if int(r_len, 16) > 32:
                return False
        elif input_type == "p2pkh":
            signature = tx["vin"][i]["scriptsig_asm"].split(' ')[1]
            r_len = signature[6:8]
            if int(r_len, 16) > 32:
                return False
        elif input_type == "v0_p2wpkh":
            r_len = tx["vin"][i]["witness"][0][6:8]
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
    prev_txouts = [tx_in["prevout"] for tx_in in tx["vin"]]
    input_script_pub_keys = [tx_out["scriptpubkey"] for tx_out in prev_txouts]
    output_script_pub_keys = [tx_out["scriptpubkey"] for tx_out in vout]

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
        outputs.append(tx_out["scriptpubkey"])

    # There are duplicate amounts, so we also have to compare
    # by scriptPubKey
    if len(set(amounts)) != len(amounts):
        if sorted(outputs) == outputs and sorted(amounts) == amounts:
            output_structure.append(OutputStructureType.BIP69)
            return output_structure
    else:
        if sorted(amounts) == amounts:
            output_structure.append(OutputStructureType.BIP69)
            return output_structure

    return output_structure

def has_multi_type_vin(tx):
    input_types = get_spending_types(tx)
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
def change_type_matched_inputs(tx):
    change_index = get_change_index(tx)
    if change_index < 0:
        return 2
    change_type = tx["vout"][change_index]["scriptpubkey_type"]

    input_types = get_spending_types(tx)
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

def address_reuse(tx):
    prev_txouts  = [tx_in["prevout"] for tx_in in tx["vin"]]

    input_script_pub_keys = [tx_out["scriptpubkey"] for tx_out in prev_txouts]
    output_script_pub_keys = [tx_out["scriptpubkey"] for tx_out in tx["vout"]]

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
    possible_wallets = {
        Wallets.BITCOIN_CORE,
        Wallets.ELECTRUM,
        Wallets.BLUE_WALLET,
        Wallets.COINBASE,
        Wallets.EXODUS,
        Wallets.TRUST,
        Wallets.TREZOR,
        Wallets.LEDGER,
    }

    reasoning = []

    # Anti-fee-sniping
    if is_anti_fee_sniping(tx) != -1:
        reasoning.append("Anti-fee-sniping")
        # discard everything but Bitcoin Core and Electrum
        possible_wallets = {
            Wallets.BITCOIN_CORE,
            Wallets.ELECTRUM,
        }
    else:
        reasoning.append("No Anti-fee-sniping")
        possible_wallets.discard(Wallets.BITCOIN_CORE)
        possible_wallets.discard(Wallets.ELECTRUM)

    # uncompressed public keys -> unknown
    if not compressed_public_keys_only(tx):
        reasoning.append("Uncompressed public key(s)")
        possible_wallets = set()
    else:
        reasoning.append("All compressed public keys")

    if tx["version"] == 1:
        reasoning.append("nVersion = 1")
        possible_wallets.discard(Wallets.BITCOIN_CORE)
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.COINBASE)
    elif tx["version"] == 2:
        reasoning.append("nVersion = 2")
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TREZOR)
        possible_wallets.discard(Wallets.TRUST)
    else: # non-standard version number
        reasoning.append("non-standard nVersion number")
        possible_wallets = set()

    if not low_r_only(tx):
        reasoning.append("Not low-r-grinding")
        possible_wallets.discard(Wallets.BITCOIN_CORE)
        possible_wallets.discard(Wallets.ELECTRUM)
    else:
        reasoning.append("Low r signatures only")

    if signals_rbf(tx):
        reasoning.append("signals RBF")
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.EXODUS)
    else:
        reasoning.append("does not signal RBF")
        possible_wallets.discard(Wallets.BITCOIN_CORE)
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TREZOR)
        possible_wallets.discard(Wallets.TRUST)
        
    sending_types = get_sending_types(tx)
    if "witness_v1_taproot" in sending_types or "v1_p2tr" in sending_types:
        reasoning.append("Sends to taproot address")
        possible_wallets.discard(Wallets.COINBASE)

    if "nulldata" in sending_types or "op_return" in sending_types:
        reasoning.append("Creates OP_RETURN output")
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TRUST)
        possible_wallets.discard(Wallets.COINBASE)

    spending_types = get_spending_types(tx)

    if "witness_v1_taproot" in spending_types or "v1_p2tr" in spending_types:
        reasoning.append("Spends taproot output")
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TRUST)

    if "witness_v0_scripthash" in spending_types or "v0_p2wsh" in spending_types:
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.TRUST)
        possible_wallets.discard(Wallets.TREZOR)

    if "pubkeyhash" in spending_types or "p2pkh" in spending_types:
        reasoning.append("Spends P2PKH output")
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.TRUST)

    if has_multi_type_vin(tx):
        reasoning.append("Has multi-type vin")
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TREZOR)
        possible_wallets.discard(Wallets.TRUST)

    change_matched_inputs = change_type_matched_inputs(tx)
    if change_matched_inputs == -1:
        reasoning.append("Change type matched outputs")
        # change matched outputs
        if Wallets.BITCOIN_CORE in possible_wallets:
            # bitcoin core is the only possible wallet
            possible_wallets = {Wallets.BITCOIN_CORE}
        else:
            possible_wallets = set() # no other wallets possible
    elif change_matched_inputs == 1:
        reasoning.append("Change type matched inputs")
        possible_wallets.discard(Wallets.BITCOIN_CORE)

    if address_reuse(tx):
        reasoning.append("Address reuse between vin and vout")
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.BITCOIN_CORE)
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TREZOR)
    else:
        reasoning.append("No address reuse between vin and vout")
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.TRUST)

    input_order = get_input_order(tx)
    output_structure = get_output_structure(tx)

    if OutputStructureType.MULTI in output_structure:
        reasoning.append("More than 2 outputs")
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TRUST)

    if OutputStructureType.BIP69 not in output_structure:
        reasoning.append("BIP-69 not followed by outputs")
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.TREZOR)
    else:
        reasoning.append("BIP-69 followed by outputs")

    if InputSortingType.SINGLE not in input_order:
        if InputSortingType.BIP69 not in input_order:
            reasoning.append("BIP-69 not followed by inputs")
            possible_wallets.discard(Wallets.ELECTRUM)
            possible_wallets.discard(Wallets.TREZOR)
        else:
            reasoning.append("BIP-69 followed by inputs")
        
        if InputSortingType.HISTORICAL not in input_order:
            reasoning.append("Inputs not ordered historically")
            possible_wallets.discard(Wallets.LEDGER)
        else:
            reasoning.append("Inputs ordered historically")

    change_index = get_change_index(tx)
    if change_index >= 0:
        if change_index != len(tx["vout"]) - 1:
            reasoning.append("Last index is not change")
            possible_wallets.discard(Wallets.LEDGER)
            possible_wallets.discard(Wallets.BLUE_WALLET)
            possible_wallets.discard(Wallets.COINBASE)

        else:
            reasoning.append("Last index is change")

    if len(possible_wallets) == 0:
        # calculate the rest of the fingerprints
        return {Wallets.OTHER}, reasoning

    return possible_wallets, reasoning

def analyze_txs(transactions):
    wallets = {}
    for wallet_type in Wallets:
        wallets[wallet_type.value] =  {'total': 0, 'txs': []}

    for txid in tqdm(transactions):
        wallet, reasoning = detect_wallet(module.get_tx(txid))
        if len(wallet) == 0:
            wallets[Wallets.OTHER.value]['total'] +=1
            wallets[Wallets.OTHER.value]['txs'].append(txid)
        elif len(wallet) == 1:
            wallets[list(wallet)[0].value]['total'] +=1
            wallets[list(wallet)[0].value]['txs'].append(txid)
        else:
            # This means that there are multiple possible wallets, and it is
            # unclear which of them it is
            wallets[Wallets.UNCLEAR.value]['total'] +=1
            wallets[Wallets.UNCLEAR.value]['txs'].append(txid)

    return wallets

def analyze_block(block_hash=None, num_of_txs=None, verbose=False):
    if not block_hash:
        block_hash = module.getbestblockhash()

    transactions = module.getblocktxs(block_hash)

    if num_of_txs:
        if len(transactions) <= num_of_txs:
            num_of_txs = None

        num_of_txs += 1

    # exclude the coinbase transaction
    transactions = transactions[1:num_of_txs]

    wallets = analyze_txs(transactions)
    if (verbose):
        return wallets

    for wallet_type in Wallets:
        wallets[wallet_type.value] = wallets[wallet_type.value]['total']
    return wallets

if __name__ == '__main__':
    block_hash = "00000000000000000004bcc50688d02a74d778201a47cc704a877d1442a58431"
    print(analyze_block(block_hash=block_hash, num_of_txs=100))
