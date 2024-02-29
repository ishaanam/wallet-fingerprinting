from typing import Any, Literal, TypeAlias, TypedDict

#
# Common
OptionalBool: TypeAlias = bool | None
OptionalBoolInt: TypeAlias = Literal[-1, 0, 1]  # #TODO: try to use OptionalBool

#
# Crypto
HexStr: TypeAlias = str  # hexadecimal string
TxId: TypeAlias = str  # tx hash
TxHex: TypeAlias = HexStr  # transaction data encoded as a hexadecimal
BlockHash: TypeAlias = str  # block hash


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
    scriptpubkey_type: str


#
# TxIn
#


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
    # vout: list[TxOutNormalized]


class TxNormalized(TypedDict):
    vin: list[TxInNormalized]
    vout: list[TxOutNormalized]


TxIn: TypeAlias = TxInNormalized
TxOut: TypeAlias = TxOutNormalized
Tx: TypeAlias = TxNormalized
