import unittest

from bitcoin_core import getrawtransaction, decoderawtransaction
from fingerprinting import *

def get_tx(txid):
    return decoderawtransaction(getrawtransaction(txid))

class TestFingerprinting(unittest.TestCase):
    def test_spending_types(self):
        tx = get_tx("60849af6e56c2ad0facd601cc5014398210898a7e6d5b9280b54f6395349663a")

        assert get_spending_types(tx) == ["pubkeyhash", "witness_v0_keyhash"]

    def test_sending_types(self):
        tx = get_tx("2fd284ed739a59ac6d6bd7f94fa2a244dd0cf88981551272b96708aebf260a57")

        assert get_sending_types(tx) == ["witness_v0_keyhash", "witness_v0_keyhash", "witness_v0_keyhash", "witness_v0_keyhash"]

    def test_compressed_public_keys(self):
        tx = get_tx("E21c826797cdb41da79dc0f65026911ea5c5b59c8cf5d115f0f62b8cb9fc1b21")

        assert get_spending_types(tx) == ["pubkeyhash", "witness_v1_taproot", "witness_v0_keyhash"]

    def test_input_order(self):
        tx = get_tx("702903c9818ac7847c9a2d9f948c9ee1ab25236821836170ef6919cd12c9e04c")
        assert get_input_order(tx) == [InputSortingType.SINGLE]

        tx = get_tx("C1094c70a9b23ca5d755234cffefca69f639d7a938f745dfd1190cc9c9d8b5ad")
        assert get_input_order(tx) == [InputSortingType.HISTORICAL]

        tx = get_tx("E21c826797cdb41da79dc0f65026911ea5c5b59c8cf5d115f0f62b8cb9fc1b21")
        assert get_input_order(tx) == [InputSortingType.DESCENDING, InputSortingType.HISTORICAL]

        tx = get_tx("C1ba2810ac35c2d17503792ee728a3df9c41c658f5442d9326eb69580bcb7dd6")
        assert get_input_order(tx) == [InputSortingType.BIP69]

    def test_low_r(self):
        assert low_r_only(get_tx("702903c9818ac7847c9a2d9f948c9ee1ab25236821836170ef6919cd12c9e04c"))
        assert not low_r_only(get_tx("43f901163b8c27567d365f56bb804bd74904bd78d58017905f3c36cac971d9b6"))
        assert not low_r_only(get_tx("Bd4a846c05c37029caf7f6cef453112eef362ca511bd6a52f9082d85b7b2f207"))

    def test_get_change_index(self):
        assert get_change_index(get_tx("43f901163b8c27567d365f56bb804bd74904bd78d58017905f3c36cac971d9b6")) == 1
        assert get_change_index(get_tx("Bd4a846c05c37029caf7f6cef453112eef362ca511bd6a52f9082d85b7b2f207")) == -1
        assert get_change_index(get_tx("d63aadc93aca05be5561d76888edf61e7f772b96fb1e43231111fe5fbcc4a601")) == -2
        # should be 1 after unnecessary input heuristic is implemented
        assert get_change_index(get_tx("60849af6e56c2ad0facd601cc5014398210898a7e6d5b9280b54f6395349663a")) == -2

    def test_get_output_structure(self):
        tx = get_tx("bc8c701594207360a409d64a9c797a46dd11a2d468948e8bb98e865249ca17e3")
        assert get_output_structure(tx) == [OutputStructureType.DOUBLE, OutputStructureType.BIP69]

        tx = get_tx("8b4e6d5fcab41058e9005f409aa505d95783b2cd52df1ec3c801cf06cac940f8")
        assert get_output_structure(tx) == [OutputStructureType.SINGLE]

        tx = get_tx("e5b278b6504297d0203a814a22239dad2b84742ec82a995c046dfef4e06fc5a4")
        assert get_output_structure(tx) == [OutputStructureType.MULTI]

    def test_anti_fee_sniping(self):
        assert is_anti_fee_sniping(get_tx("d63aadc93aca05be5561d76888edf61e7f772b96fb1e43231111fe5fbcc4a601")) == -1
        assert is_anti_fee_sniping(get_tx("5d857401648a667303cde43295bce1326e6329353eac3dddf15b151e701405e7")) == 1

if __name__ == '__main__':
    unittest.main()
