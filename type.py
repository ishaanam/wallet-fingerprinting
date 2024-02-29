from typing import Any, Literal, TypeAlias, TypedDict

#
# Common
OptionalBool: TypeAlias = bool | None
ThreeInt: TypeAlias = Literal[-1, 0, 1]  # #TODO: try to use OptionalBool
FourInt: TypeAlias = Literal[-1, 0, 1, 2]  # #TODO: try to type better

#
# Crypto
HexStr: TypeAlias = str  # hexadecimal string
TxId: TypeAlias = str  # tx hash
TxHex: TypeAlias = HexStr  # transaction data encoded as a hexadecimal
BlockHash: TypeAlias = str  # block hash
ValueType: TypeAlias = int
# #TODO: check if ValueType is float, Decimal or int  # value in BTC

# Unfinished type aliases #TODO
ScriptPubKeyType: TypeAlias = (
    str
    | Literal[
        "pubkeyhash",
        "scripthash",
        "witness_v0_keyhash",
        "witness_v0_scripthash",
        "witness_v1_taproot",
        "v1_p2tr",
    ]
)


class ScriptPubKey(TypedDict):
    hex: str
    address: str
    type: str


class TxOutNotNormalized(TypedDict):
    scriptPubKey: ScriptPubKey
    address: str
    type: str


class TxOutNormalized(TypedDict):
    scriptpubkey: HexStr
    scriptpubkey_address: str
    scriptpubkey_type: ScriptPubKeyType
    value: ValueType


# TxIn


class TxInNotNormalized(TypedDict):
    scriptsig: str
    witness: list[str]
    prevout: dict[str, Any]
    txid: TxId
    vout: list[TxOutNotNormalized]
    scriptSig: dict[str, Any]
    txinwitness: list[str]


class TxNotNormalized(TypedDict):
    vin: list[TxInNotNormalized]
    vout: list[TxOutNotNormalized]


class TxInNormalized(TypedDict):
    scriptsig_asm: str
    scriptsig: str
    witness: list[str]
    prevout: TxOutNormalized
    txid: TxId
    vout: list[TxOutNormalized]  # #TODO:should not be read since we have prevout
    # #FIX: below not implemented in bitcoin_core.py
    sequence: int


class TxNormalized(TypedDict):
    vin: list[TxInNormalized]
    vout: list[TxOutNormalized]
    # #FIX: below not implemented in bitcoin_core.py
    locktime: int
    version: int
    txid: TxId


TxIn: TypeAlias = TxInNormalized
TxOut: TypeAlias = TxOutNormalized
Tx: TypeAlias = TxNormalized
