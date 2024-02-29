from enum import Enum
from typing import Any, Literal, TypeAlias, TypedDict

#
# Common
OptionalBool: TypeAlias = bool | None
HexStr: TypeAlias = str  # hexadecimal string
ThreeInts: TypeAlias = Literal[-1, 0, 1]  # #TODO: try to use OptionalBool
FourInts: TypeAlias = Literal[-1, 0, 1, 2]  # #TODO: try to type better

#
# Crypto
BlockId: TypeAlias = str  # block hash
TxId: TypeAlias = str  # tx hash
TxHex: TypeAlias = HexStr  # transaction data encoded as a hexadecimal
ValueType: TypeAlias = float
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


# Transactions: TxOut, TxIn, Tx


class TxOutNotNormalized(TypedDict):
    scriptPubKey: ScriptPubKey
    address: str
    type: str
    value: ValueType


class TxOutNormalized(TypedDict):
    scriptpubkey: HexStr
    scriptpubkey_address: str
    scriptpubkey_type: ScriptPubKeyType
    value: ValueType


class TxInNotNormalized(TypedDict):
    witness: list[str]
    prevout: dict[str, Any]
    txid: TxId
    vout: list[TxOutNotNormalized]
    scriptSig: dict[str, Any]
    txinwitness: list[str]
    locktime: int
    sequence: int


class TxInNormalized(TypedDict):
    scriptsig_asm: str
    scriptsig: str
    witness: list[str]
    prevout: TxOutNormalized
    txid: TxId
    vout: list[TxOutNormalized]  # #TODO:should not be read since we have prevout
    locktime: int
    sequence: int


class TxNotNormalized(TypedDict):
    """
    Normalized here refers to "bitcoin_core.py" implementation,
    not "mempool_space.py"
    """

    vin: list[TxInNotNormalized]
    vout: list[TxOutNotNormalized]
    # #TODO: base class
    locktime: int
    version: int
    txid: TxId


class TxNormalized(TypedDict):
    vin: list[TxInNormalized]
    vout: list[TxOutNormalized]
    # #TODO: base class
    locktime: int
    version: int
    txid: TxId


TxIn: TypeAlias = TxInNormalized
TxOut: TypeAlias = TxOutNormalized
Tx: TypeAlias = TxNormalized


#
# SUPPORTIVE CLASSES
#


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


class WalletAnalyzeResult(dict[Wallets, list[TxId]]):
    """
    TODO: total in WalletAnalyzeEntry is redundant, we can use len(txs)
    """

    def __init__(self) -> None:
        super().__init__({wallet: [] for wallet in Wallets})

    @property
    def counter(self) -> dict[Wallets, int]:
        """
        Return the counter of transactions only

        TODO: use Counter from collections, and change __str__ method
        """
        return {k: len(v) for k, v in self.items()}

    @property
    def shorten(self) -> dict[str, int]:
        """
        return plain dict with string-int pairs
        """
        return {k.value: c for k, c in self.counter.items()}

    def __str__(self) -> str:
        """
        For "user-friendly" output, we should show the count of txn only
        """
        return str(self.shorten)
