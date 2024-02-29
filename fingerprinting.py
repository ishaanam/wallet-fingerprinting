from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Optional, Sequence, Union, cast

from tqdm.auto import tqdm

from fetch_txs import get_confirmation_height, module
from type import (
    BlockId,
    FourInts,
    ScriptPubKeyType,
    ThreeInts,
    Tx,
    TxId,
    ValueType,
    WalletAnalyzeResult,
    Wallets,
)


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


@dataclass
class WalletReasoning:
    """
    A class to represent reasoning for wallet detection with methods
    to validate the reasoning state and convert it to a readable format.

    Attributes:
    ----------
    Each attribute represents a specific criterion used in wallet detection.
    The attributes are optional and can be either True, False, or not set.
    """

    ANTI_FEE_SNIPING: Optional[bool] = field(
        default=None, metadata={"description": "Anti-fee-sniping"}
    )
    UNCOMPRESSED_PUBLIC_KEYS: Optional[bool] = field(
        default=None, metadata={"description": "Uncompressed public key(s)"}
    )
    TX_VERSION: Optional[Union[int, Literal["Unknown Version"]]] = field(default=None)
    LOW_R_SIGNATURES: Optional[bool] = field(default=None)
    SIGNALS_RBF: Optional[bool] = field(default=None)
    FROM_TAPROOT: Optional[bool] = field(default=None)
    TO_TAPROOT: Optional[bool] = field(default=None)
    TO_OP_RETURN: Optional[bool] = field(default=None)
    FROM_P2WSH: Optional[bool] = field(default=None)
    TO_P2WSH: Optional[bool] = field(default=None)
    FROM_P2PKH: Optional[bool] = field(default=None)
    CHANGE_MATCHED_OUTPUTS: Optional[bool] = field(default=None)
    CHANGE_MATCHED_INPUTS: Optional[bool] = field(default=None)
    ADDRESS_REUSE: Optional[bool] = field(default=None)
    CHANGE_LAST_INDEX: Optional[bool] = field(default=None)
    HAS_MULTI_TYPE_VIN: Optional[bool] = field(default=None)
    MULTI_OUTPUTS: Optional[bool] = field(default=None)
    BIP69_OUTPUT: Optional[bool] = field(default=None)
    BIP69_INPUT: Optional[bool] = field(default=None)
    HISTORICALLY_ORDERED_INPUT: Optional[bool] = field(default=None)
    VALID_NULL_KEYS = (
        "FROM_TAPROOT",
        "TO_TAPROOT",
        "TO_OP_RETURN",
        "FROM_P2PKH",
        "FROM_P2WSH",
        "TO_P2WSH",
        "CHANGE_MATCHED_OUTPUTS",  # #TODO: change_matched_inputs not exhaustive, should handle 0 and 2
        "HAS_MULTI_TYPE_VIN",  # #TODO: not exhaustive HAS_MULTI_TYPE_VIN
        "MULTI_OUTPUTS",  # #TODO: not exhaustive MULTI_OUTPUTS
        "CHANGE_LAST_INDEX",  # #TODO: ref and check logic of change_index, NGE_LAST_INDEX
        "BIP69_INPUT",  # #TODO: ref and check logic of InputSortingType.BIP69| ~.HISTORICAL
        "CHANGE_MATCHED_INPUTS",  # TODO: change_matched_inputs not exhaustive, should handle 0 and 2
        "HISTORICALLY_ORDERED_INPUT",  # #TODO: ref and check logic of InputSortingType.BIP69| ~.HISTORICAL
    )

    def __validate_completeness(self) -> bool:
        """
        Validates that all attributes of the WalletReasoning instance are defined and not None.
        """
        invalid_keys = list[str]()
        for field_name, field_value in self.__dict__.items():
            if field_name in self.VALID_NULL_KEYS:
                continue
            if field_value is None:
                invalid_keys.append(field_name)
        if invalid_keys:
            print(f"Reasoning Validation failed: {invalid_keys=} are None")
            return False
        return True

    def to_readable_format(self) -> list[str]:
        """
        Converts the reasoning into a readable format suitable for logging or display.
        """
        if not self.__validate_completeness():
            return ["Incomplete reasoning"]
        readable_list = list[str]()
        for field_name, field_value in self.__dict__.items():
            if field_name == "VALID_NULL_KEYS":
                continue
            description = self.__dataclass_fields__[field_name].metadata.get(
                "description", field_name
            )
            readable_list.append(f"{description}: {'Yes' if field_value else 'No'}")
        return readable_list


def get_spending_types(tx: Tx) -> list[ScriptPubKeyType]:
    types = list[ScriptPubKeyType]()
    for tx_in in tx["vin"]:
        types.append(tx_in["prevout"]["scriptpubkey_type"])
    return types


def get_sending_types(tx: Tx) -> list[ScriptPubKeyType]:
    types = list[ScriptPubKeyType]()
    for tx_out in tx["vout"]:
        types.append(tx_out["scriptpubkey_type"])
    return types


def compressed_public_keys_only(tx: Tx) -> bool:
    input_types = get_spending_types(tx)
    for i, input_type in enumerate(input_types):
        if input_type == "witness_v0_keyhash" or input_type == "v0_p2wpkh":
            if tx["vin"][i]["witness"][1][1] == "4":
                return False
        elif input_type == "pubkeyhash" or input_type == "p2pkh":
            if (
                tx["vin"][i]["scriptsig_asm"][
                    tx["vin"][i]["scriptsig_asm"].find(" ") + 2
                ]
                == "4"
            ):
                return False
    return True


def get_input_order(tx: Tx) -> list[InputSortingType]:
    if len(tx["vin"]) == 1:
        return [InputSortingType.SINGLE]
    sorting_types = list[InputSortingType]()
    amounts = list[ValueType]()
    prevouts = list[TxId]()

    for tx_in in tx["vin"]:
        prevouts.append(f"{tx_in['txid']}:{tx_in['vout']}")
        amounts.append(tx_in["prevout"]["value"])

    if sorted(amounts) == amounts:
        sorting_types.append(InputSortingType.ASCENDING)
    if sorted(amounts)[::-1] == amounts:
        sorting_types.append(InputSortingType.DESCENDING)

    if sorted(prevouts) == prevouts:
        sorting_types.append(InputSortingType.BIP69)

    # #TODO-1: refactor logic of prevout_conf_heights
    prevout_conf_heights = dict[TxId, int | None](
        {prevout: None for prevout in prevouts}
    )

    for prevout in prevouts:
        txid = prevout[0 : prevout.find(":")]
        conf_height = get_confirmation_height(txid)
        if conf_height != -1:
            prevout_conf_heights[prevout] = conf_height
        else:
            del prevout_conf_heights[prevout]  # remove the None values
    prevout_conf_heights = cast(dict[TxId, int], prevout_conf_heights)
    ordered_conf_heights = list(prevout_conf_heights.values())
    if ordered_conf_heights == sorted(ordered_conf_heights):
        sorting_types.append(InputSortingType.HISTORICAL)
    # #TODO-1: refactor logic of prevout_conf_heights #END

    if len(sorting_types) == 0:
        sorting_types.append(InputSortingType.UNKNOWN)
    return sorting_types


# Returns false if there is an r value of more than 32 bytes
def low_r_only(tx: Tx) -> bool:
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
            signature = tx["vin"][i]["scriptsig_asm"].split(" ")[1]
            r_len = signature[6:8]
            if int(r_len, 16) > 32:
                return False
        elif input_type == "v0_p2wpkh":
            r_len = tx["vin"][i]["witness"][0][6:8]
            if int(r_len, 16) > 32:
                return False

    return True


def get_change_index(tx: Tx) -> int:
    vout = tx["vout"]

    # if single, return -1 as index
    if len(vout) == 1:
        return -1

    input_types = get_spending_types(tx)
    output_types = get_sending_types(tx)

    # if all inputs are of the same type, and only one output of the outputs is of that type,
    if len(set(input_types)) == 1:
        if output_types.count(input_types[0]) == 1:
            return output_types.index(input_types[0])

    # same as one of the input addresses
    prev_txouts = [tx_in["prevout"] for tx_in in tx["vin"]]
    input_script_pub_keys = [tx_out["scriptpubkey"] for tx_out in prev_txouts]
    output_script_pub_keys = [tx_out["scriptpubkey"] for tx_out in vout]

    shared_address = list(
        set(output_script_pub_keys).intersection(set(input_script_pub_keys))
    )

    if (
        len(shared_address) == 1
        and output_script_pub_keys.count(shared_address[0]) == 1
    ):
        return output_script_pub_keys.index(shared_address[0])

    # TODO: Unnecessary Input Heuristic: https://en.bitcoin.it/wiki/Privacy#Change_address_detection
    # input_amounts = [tx_out["value"] for tx_out in prev_txouts]

    output_amounts = [
        int(tx_out["value"] * 100000000) for tx_out in vout
    ]  # stored as satoshis

    possible_index = list[int]()

    for i, amount in enumerate(output_amounts):
        if amount % 100 != 0:
            possible_index.append(i)

    if len(possible_index) == 1:
        return possible_index[0]

    # else inconclusive, return -2
    return -2


def get_output_structure(tx: Tx) -> list[OutputStructureType]:
    vout = tx["vout"]
    if len(vout) == 1:
        return [OutputStructureType.SINGLE]

    output_structure = list[OutputStructureType]()

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
    amounts = list[ValueType]()
    outputs = list[ScriptPubKeyType]()

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


def has_multi_type_vin(tx: Tx) -> bool:
    input_types = get_spending_types(tx)
    if len(set(input_types)) == 1:
        return False
    return True


# -1 if definitely not
# 0 if possible
# 1 if very likely
# Note: also add if there isn't OP_CLTV in one of the inputs
def is_anti_fee_sniping(tx: Tx) -> ThreeInts:
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
def change_type_matched_inputs(tx: Tx) -> FourInts:
    change_index = get_change_index(tx)
    if change_index < 0:
        return 2
    change_type = tx["vout"][change_index]["scriptpubkey_type"]

    input_types = get_spending_types(tx)
    output_types = get_sending_types(tx)
    output_types.remove(change_type)

    if change_type in output_types:
        if change_type in input_types:
            return 0  # both
        return -1
    else:
        if change_type in input_types:
            return 1
        return 0  # neither


def address_reuse(tx: Tx) -> bool:
    prev_txouts = [tx_in["prevout"] for tx_in in tx["vin"]]

    input_script_pub_keys = [tx_out["scriptpubkey"] for tx_out in prev_txouts]
    output_script_pub_keys = [tx_out["scriptpubkey"] for tx_out in tx["vout"]]

    shared_address = list(
        set(output_script_pub_keys).intersection(set(input_script_pub_keys))
    )
    if shared_address:
        return True
    return False


def signals_rbf(tx: Tx) -> bool:
    for tx_in in tx["vin"]:
        if tx_in["sequence"] < 0xFFFFFFFF:
            return True
    return False


def spends_unconfirmed(tx: Tx) -> bool:
    """
    returns true if any of the inputs are unconfirmed

    Args:
    tx (Tx): the transaction to check

    Returns:
    bool: True if any of the inputs are unconfirmed

    TODO:
    need historical mempool data for this to be completely accurate
    """
    raise NotImplementedError("spends_unconfirmed is not implemented")


def detect_wallet(tx: Tx) -> tuple[set[Wallets], list[str]]:
    possible_wallets: set[Wallets] = {
        Wallets.BITCOIN_CORE,
        Wallets.ELECTRUM,
        Wallets.BLUE_WALLET,
        Wallets.COINBASE,
        Wallets.EXODUS,
        Wallets.TRUST,
        Wallets.TREZOR,
        Wallets.LEDGER,
    }
    new_reason = WalletReasoning()
    reasoning = list[str]()

    # Anti-fee-sniping
    if is_anti_fee_sniping(tx) != -1:
        # reasoning.append("Anti-fee-sniping")
        new_reason.ANTI_FEE_SNIPING = True
        # discard everything but Bitcoin Core and Electrum
        possible_wallets = {
            Wallets.BITCOIN_CORE,
            Wallets.ELECTRUM,
        }
    else:
        # reasoning.append("No Anti-fee-sniping")
        new_reason.ANTI_FEE_SNIPING = False
        possible_wallets.discard(Wallets.BITCOIN_CORE)
        possible_wallets.discard(Wallets.ELECTRUM)

    # uncompressed public keys -> unknown
    if not compressed_public_keys_only(tx):
        new_reason.UNCOMPRESSED_PUBLIC_KEYS = True
        # reasoning.append("Uncompressed public key(s)")
        possible_wallets = set()
    else:
        new_reason.UNCOMPRESSED_PUBLIC_KEYS = False
        # reasoning.append("All compressed public keys")

    if tx["version"] == 1:
        new_reason.TX_VERSION = 1
        # reasoning.append("nVersion = 1")
        possible_wallets.discard(Wallets.BITCOIN_CORE)
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.COINBASE)
    elif tx["version"] == 2:
        new_reason.TX_VERSION = 2
        # reasoning.append("nVersion = 2")
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TREZOR)
        possible_wallets.discard(Wallets.TRUST)
    else:  # non-standard version number
        new_reason.TX_VERSION = "Unknown Version"
        # reasoning.append("non-standard nVersion number")
        possible_wallets = set()

    if not low_r_only(tx):
        new_reason.LOW_R_SIGNATURES = False
        # reasoning.append("Not low-r-grinding")
        possible_wallets.discard(Wallets.BITCOIN_CORE)
        possible_wallets.discard(Wallets.ELECTRUM)
    else:
        new_reason.LOW_R_SIGNATURES = True
        # reasoning.append("Low r signatures only")

    if signals_rbf(tx):
        new_reason.SIGNALS_RBF = True
        # reasoning.append("signals RBF")
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.EXODUS)
    else:
        new_reason.SIGNALS_RBF = False
        # reasoning.append("does not signal RBF")
        possible_wallets.discard(Wallets.BITCOIN_CORE)
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TREZOR)
        possible_wallets.discard(Wallets.TRUST)

    sending_types = get_sending_types(tx)
    if "witness_v1_taproot" in sending_types or "v1_p2tr" in sending_types:
        new_reason.TO_TAPROOT = True
        # reasoning.append("Sends to taproot address")
        possible_wallets.discard(Wallets.COINBASE)

    if "nulldata" in sending_types or "op_return" in sending_types:
        new_reason.TO_OP_RETURN = True
        # reasoning.append("Creates OP_RETURN output")
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TRUST)
        possible_wallets.discard(Wallets.COINBASE)

    spending_types = get_spending_types(tx)

    if "witness_v1_taproot" in spending_types or "v1_p2tr" in spending_types:
        new_reason.FROM_TAPROOT = True
        # reasoning.append("Spends taproot output")
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TRUST)

    if "witness_v0_scripthash" in spending_types or "v0_p2wsh" in spending_types:
        new_reason.FROM_P2WSH = True
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.TRUST)
        possible_wallets.discard(Wallets.TREZOR)

    if "pubkeyhash" in spending_types or "p2pkh" in spending_types:
        new_reason.FROM_P2PKH = True
        # reasoning.append("Spends P2PKH output")
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.TRUST)

    if has_multi_type_vin(tx):
        new_reason.HAS_MULTI_TYPE_VIN = True
        # reasoning.append("Has multi-type vin")
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TREZOR)
        possible_wallets.discard(Wallets.TRUST)

    change_matched_inputs = change_type_matched_inputs(tx)
    if change_matched_inputs == -1:
        new_reason.CHANGE_MATCHED_OUTPUTS = True
        # reasoning.append("Change type matched outputs")
        # change matched outputs
        if Wallets.BITCOIN_CORE in possible_wallets:
            # bitcoin core is the only possible wallet
            possible_wallets = {Wallets.BITCOIN_CORE}
        else:
            possible_wallets = set()  # no other wallets possible
    elif change_matched_inputs == 1:
        new_reason.CHANGE_MATCHED_INPUTS = True
        # reasoning.append("Change type matched inputs")
        possible_wallets.discard(Wallets.BITCOIN_CORE)
    # else # #TODO: change_matched_inputs not exhaustive, should handle 0 and 2

    if address_reuse(tx):
        new_reason.ADDRESS_REUSE = True
        # reasoning.append("Address reuse between vin and vout")
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.BITCOIN_CORE)
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.BLUE_WALLET)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TREZOR)
    else:
        new_reason.ADDRESS_REUSE = False
        # reasoning.append("No address reuse between vin and vout")
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.TRUST)

    input_order = get_input_order(tx)
    output_structure = get_output_structure(tx)

    if OutputStructureType.MULTI in output_structure:
        new_reason.MULTI_OUTPUTS = True
        # reasoning.append("More than 2 outputs")
        possible_wallets.discard(Wallets.COINBASE)
        possible_wallets.discard(Wallets.EXODUS)
        possible_wallets.discard(Wallets.LEDGER)
        possible_wallets.discard(Wallets.TRUST)

    if OutputStructureType.BIP69 not in output_structure:
        new_reason.BIP69_OUTPUT = False
        # reasoning.append("BIP-69 not followed by outputs")
        possible_wallets.discard(Wallets.ELECTRUM)
        possible_wallets.discard(Wallets.TREZOR)
    else:
        new_reason.BIP69_OUTPUT = True
        # reasoning.append("BIP-69 followed by outputs")

    # #TODO: ref and check logic of InputSortingType.BIP69| ~.HISTORICAL
    if InputSortingType.SINGLE not in input_order:
        if InputSortingType.BIP69 not in input_order:
            new_reason.BIP69_INPUT = False
            # reasoning.append("BIP-69 not followed by inputs")
            possible_wallets.discard(Wallets.ELECTRUM)
            possible_wallets.discard(Wallets.TREZOR)
        else:
            new_reason.BIP69_INPUT = True
            # reasoning.append("BIP-69 followed by inputs")

        if InputSortingType.HISTORICAL not in input_order:
            new_reason.HISTORICALLY_ORDERED_INPUT = False
            # reasoning.append("Inputs not ordered historically")
            possible_wallets.discard(Wallets.LEDGER)
        else:
            new_reason.HISTORICALLY_ORDERED_INPUT = True
            # reasoning.append("Inputs ordered historically")

    change_index = get_change_index(tx)
    # #TODO: ref and check logic of change_index, NGE_LAST_INDEX
    if change_index >= 0:
        if change_index != len(tx["vout"]) - 1:
            new_reason.CHANGE_LAST_INDEX = False
            # reasoning.append("Last index is not change")
            possible_wallets.discard(Wallets.LEDGER)
            possible_wallets.discard(Wallets.BLUE_WALLET)
            possible_wallets.discard(Wallets.COINBASE)
        else:
            new_reason.CHANGE_LAST_INDEX = True
            # reasoning.append("Last index is change")

    # #FIX: I broke the logic
    if len(possible_wallets) == 0:
        # calculate the rest of the fingerprints
        return {Wallets.OTHER}, reasoning

    return possible_wallets, new_reason.to_readable_format()


def analyze_txs(transactions: Sequence[TxId]) -> WalletAnalyzeResult:
    wallets = WalletAnalyzeResult()
    for wallet_type in Wallets:
        wallets[wallet_type] = {"total": 0, "txs": []}

    for txid in tqdm(transactions):
        wallet, _reasoning = detect_wallet(module.get_tx(txid))
        # #TODO-DESIGN: case==0 not needed? : already handled in detect_wallet
        if len(wallet) == 0:
            wallets[Wallets.OTHER]["total"] += 1
            wallets[Wallets.OTHER]["txs"].append(txid)
        elif len(wallet) == 1:
            wallets[list(wallet)[0]]["total"] += 1
            wallets[list(wallet)[0]]["txs"].append(txid)
        # #TODO-DESIGN: should handle in detect_wallet too?
        else:
            # This means that there are multiple possible wallets, and it is
            # unclear which of them it is
            wallets[Wallets.UNCLEAR]["total"] += 1
            wallets[Wallets.UNCLEAR]["txs"].append(txid)

    return wallets


def analyze_block(
    block_hash: BlockId = "",
    num_of_txs: int = 0,  # analyze first num_of_txs transactions, or all if 0
) -> WalletAnalyzeResult:
    if block_hash == "":
        block_hash = module.getbestblockhash()
    transactions = module.getblocktxs(block_hash)

    # exclude the coinbase transaction
    transactions = transactions[1:]
    if num_of_txs != 0:
        transactions = transactions[:num_of_txs]

    txs_wallets_result = analyze_txs(transactions)
    # #FIX: fix all calls to this function due to this change
    # if verbose:
    return txs_wallets_result

    # #TODO: add a readable format for the result
    # wallets: dict[str, int] = dict()
    # for wallet_type in Wallets:
    #     wallets[wallet_type.name] = txs_wallets_result[wallet_type]["total"]
    # return wallets


if __name__ == "__main__":
    block_hash = "00000000000000000004bcc50688d02a74d778201a47cc704a877d1442a58431"
    print(analyze_block(block_hash=block_hash, num_of_txs=100))
