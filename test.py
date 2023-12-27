import unittest

from fetch_txs import module
from fingerprinting import *

class TestFingerprinting(unittest.TestCase):
    def test_spending_types(self):
        tx = module.get_tx("60849af6e56c2ad0facd601cc5014398210898a7e6d5b9280b54f6395349663a")

        spending_types = get_spending_types(tx)
        assert spending_types == ["pubkeyhash", "witness_v0_keyhash"] or spending_types == ["p2pkh", "v0_p2wpkh"]

        tx = module.get_tx("E21c826797cdb41da79dc0f65026911ea5c5b59c8cf5d115f0f62b8cb9fc1b21")

        spending_types = get_spending_types(tx)
        assert spending_types == ["pubkeyhash", "witness_v1_taproot", "witness_v0_keyhash"] or spending_types == ["p2pkh", "v1_p2tr", "v0_p2wpkh"]

    def test_sending_types(self):
        tx = module.get_tx("2fd284ed739a59ac6d6bd7f94fa2a244dd0cf88981551272b96708aebf260a57")

        sending_types = get_sending_types(tx)
        assert sending_types == ["witness_v0_keyhash", "witness_v0_keyhash", "witness_v0_keyhash", "witness_v0_keyhash"] or sending_types == ["v0_p2wpkh", "v0_p2wpkh", "v0_p2wpkh", "v0_p2wpkh"]

    def test_has_multi_type_vin(self):
        assert not has_multi_type_vin(module.get_tx("5d857401648a667303cde43295bce1326e6329353eac3dddf15b151e701405e7"))
        assert has_multi_type_vin(module.get_tx("E21c826797cdb41da79dc0f65026911ea5c5b59c8cf5d115f0f62b8cb9fc1b21"))

    def test_input_order(self):
        tx = module.get_tx("702903c9818ac7847c9a2d9f948c9ee1ab25236821836170ef6919cd12c9e04c")
        assert get_input_order(tx) == [InputSortingType.SINGLE]

        tx = module.get_tx("C1094c70a9b23ca5d755234cffefca69f639d7a938f745dfd1190cc9c9d8b5ad")
        assert get_input_order(tx) == [InputSortingType.HISTORICAL]

        tx = module.get_tx("E21c826797cdb41da79dc0f65026911ea5c5b59c8cf5d115f0f62b8cb9fc1b21")
        assert get_input_order(tx) == [InputSortingType.DESCENDING, InputSortingType.HISTORICAL]

        tx = module.get_tx("C1ba2810ac35c2d17503792ee728a3df9c41c658f5442d9326eb69580bcb7dd6")
        assert get_input_order(tx) == [InputSortingType.BIP69]

    def test_low_r(self):
        assert low_r_only(module.get_tx("702903c9818ac7847c9a2d9f948c9ee1ab25236821836170ef6919cd12c9e04c"))
        assert not low_r_only(module.get_tx("43f901163b8c27567d365f56bb804bd74904bd78d58017905f3c36cac971d9b6"))
        assert not low_r_only(module.get_tx("Bd4a846c05c37029caf7f6cef453112eef362ca511bd6a52f9082d85b7b2f207"))

    def test_get_change_index(self):
        assert get_change_index(module.get_tx("43f901163b8c27567d365f56bb804bd74904bd78d58017905f3c36cac971d9b6")) == 1
        assert get_change_index(module.get_tx("Bd4a846c05c37029caf7f6cef453112eef362ca511bd6a52f9082d85b7b2f207")) == -1
        assert get_change_index(module.get_tx("d63aadc93aca05be5561d76888edf61e7f772b96fb1e43231111fe5fbcc4a601")) == -2
        # should be 1 after unnecessary input heuristic is implemented
        assert get_change_index(module.get_tx("60849af6e56c2ad0facd601cc5014398210898a7e6d5b9280b54f6395349663a")) == -2

    def test_get_output_structure(self):
        tx = module.get_tx("bc8c701594207360a409d64a9c797a46dd11a2d468948e8bb98e865249ca17e3")
        assert get_output_structure(tx) == [OutputStructureType.DOUBLE, OutputStructureType.BIP69]

        tx = module.get_tx("8b4e6d5fcab41058e9005f409aa505d95783b2cd52df1ec3c801cf06cac940f8")
        assert get_output_structure(tx) == [OutputStructureType.SINGLE]

        tx = module.get_tx("e5b278b6504297d0203a814a22239dad2b84742ec82a995c046dfef4e06fc5a4")
        assert get_output_structure(tx) == [OutputStructureType.MULTI, OutputStructureType.CHANGE_LAST]

    def test_anti_fee_sniping(self):
        assert is_anti_fee_sniping(module.get_tx("d63aadc93aca05be5561d76888edf61e7f772b96fb1e43231111fe5fbcc4a601")) == -1
        assert is_anti_fee_sniping(module.get_tx("5d857401648a667303cde43295bce1326e6329353eac3dddf15b151e701405e7")) == 1

    def test_change_type_matched_inputs(self):
        assert change_type_matched_inputs(module.get_tx("01d5bfed27b98cd049d5e3547e93a447df6cbfa1a1d64c33aff427bef8b3cec4")) == 1

    def test_signals_rbf(self):
        assert not signals_rbf(module.get_tx("Bd4a846c05c37029caf7f6cef453112eef362ca511bd6a52f9082d85b7b2f207"))
        assert signals_rbf(module.get_tx("Af39337032ec9d37aa91e41b152c1522cddc2070c08b06a1aaf5fe6ab6285a04"))

    def test_address_reuse(self):
        assert address_reuse(module.get_tx("43f901163b8c27567d365f56bb804bd74904bd78d58017905f3c36cac971d9b6"))
        assert not address_reuse(module.get_tx("1849118e584418ef9649e88e3b44a6ab6a6b06440fe7b1c51a1e76f16e72cefa"))

    def test_bitcoin_core(self):
        wallet, reasoning = detect_wallet(module.get_tx("ba6e613d7894e81f369bdf1c77c57c772245643bef256f9df1e23bc0225b2e81"))
        assert wallet == {Wallets.BITCOIN_CORE}

    def test_electrum(self):
        wallet, reasoning = detect_wallet(module.get_tx("5d857401648a667303cde43295bce1326e6329353eac3dddf15b151e701405e7"))
        assert wallet == {Wallets.ELECTRUM}

    def test_blue_wallet(self):
        wallet, reasoning = detect_wallet(module.get_tx("e5b278b6504297d0203a814a22239dad2b84742ec82a995c046dfef4e06fc5a4"))
        assert wallet == {Wallets.BLUE_WALLET}

        wallet, reasoning = detect_wallet(module.get_tx("2fd284ed739a59ac6d6bd7f94fa2a244dd0cf88981551272b96708aebf260a57"))
        assert wallet == {Wallets.BLUE_WALLET}

        wallet, reasoning = detect_wallet(module.get_tx("1bf659e17568e48d6f47bb5470bc8df567cfe89d79c6e38cafbe798f43d5da22"))
        assert wallet == {Wallets.BLUE_WALLET}

        wallet, reasoning = detect_wallet(module.get_tx("702903c9818ac7847c9a2d9f948c9ee1ab25236821836170ef6919cd12c9e04c"))
        assert wallet == {Wallets.BLUE_WALLET}

        wallet, reasoning = detect_wallet(module.get_tx("Af39337032ec9d37aa91e41b152c1522cddc2070c08b06a1aaf5fe6ab6285a04"))
        assert wallet == {Wallets.BLUE_WALLET}

    def test_coinbase(self):
        wallet, reasoning = detect_wallet(module.get_tx("Bd4a846c05c37029caf7f6cef453112eef362ca511bd6a52f9082d85b7b2f207"))
        assert wallet == {Wallets.COINBASE}

        wallet, reasoning = detect_wallet(module.get_tx("60849af6e56c2ad0facd601cc5014398210898a7e6d5b9280b54f6395349663a"))
        assert wallet == {Wallets.COINBASE}

    def test_exodus(self):
        wallet, reasoning = detect_wallet(module.get_tx("6f8c37db6ed88bfd0fd483963ebf06c5557326f8d2a3617af5ceba878442e1ad"))
        assert wallet == {Wallets.EXODUS}

    def test_trust(self):
        wallet, reasoning = detect_wallet(module.get_tx("43f901163b8c27567d365f56bb804bd74904bd78d58017905f3c36cac971d9b6"))
        assert wallet == {Wallets.TRUST}

    def test_trezor(self):
        wallet, reasoning = detect_wallet(module.get_tx("C1ba2810ac35c2d17503792ee728a3df9c41c658f5442d9326eb69580bcb7dd6"))
        assert wallet == {Wallets.TREZOR}

        wallet, reasoning = detect_wallet(module.get_tx("bc8c701594207360a409d64a9c797a46dd11a2d468948e8bb98e865249ca17e3"))
        assert wallet == {Wallets.TREZOR}

        wallet, reasoning = detect_wallet(module.get_tx("87670b12778d17c759db459479d66acfd1c4d444094270991d8e1de09a56cc7c"))
        assert wallet == {Wallets.TREZOR}

    def test_ledger(self):
        wallet, reasoning = detect_wallet(module.get_tx("01d5bfed27b98cd049d5e3547e93a447df6cbfa1a1d64c33aff427bef8b3cec4"))
        assert wallet == {Wallets.LEDGER}

        wallet, reasoning = detect_wallet(module.get_tx("C1094c70a9b23ca5d755234cffefca69f639d7a938f745dfd1190cc9c9d8b5ad"))
        assert wallet == {Wallets.LEDGER}

        wallet, reasoning = detect_wallet(module.get_tx("b2863a85081cd113094d50878153fab5c3160999e5fd2e044782b851c4dc72e1"))
        assert wallet == {Wallets.LEDGER}

        wallet, reasoning = detect_wallet(module.get_tx("047b1779fceb28852d890fd36bbc0481ed7aa8eb8b73fc1ab19d7707780c041d"))
        assert wallet == {Wallets.LEDGER}

if __name__ == '__main__':
    unittest.main()
