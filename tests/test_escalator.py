"""escalator.py 단위 테스트."""

from f2md.escalator import DEFAULT_MODE_CHAIN, get_chain, next_mode


class TestNextMode:
    def test_standard_to_ocr(self):
        assert next_mode("standard") == "ocr"

    def test_ocr_to_high_accuracy(self):
        assert next_mode("ocr") == "high_accuracy"

    def test_high_accuracy_returns_none(self):
        assert next_mode("high_accuracy") is None

    def test_unknown_mode_returns_none(self):
        assert next_mode("nonexistent") is None

    def test_custom_chain(self):
        chain = ["a", "b", "c"]
        assert next_mode("a", chain) == "b"
        assert next_mode("b", chain) == "c"
        assert next_mode("c", chain) is None

    def test_single_element_chain(self):
        assert next_mode("only", ["only"]) is None

    def test_default_chain_order(self):
        assert DEFAULT_MODE_CHAIN == ["standard", "ocr", "high_accuracy"]


class TestGetChain:
    def test_returns_default_when_no_cfg(self):
        assert get_chain(None) == DEFAULT_MODE_CHAIN

    def test_returns_cfg_chain(self):
        cfg = {"modes": {"chain": ["standard", "ocr"]}}
        assert get_chain(cfg) == ["standard", "ocr"]

    def test_returns_default_when_modes_missing(self):
        assert get_chain({}) == DEFAULT_MODE_CHAIN
