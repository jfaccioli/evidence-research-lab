import pytest

from crl.production.strategies import assert_approved, is_approved, list_approved


def test_approved_empty():
    assert list_approved() == []
    assert is_approved("hyp_anything") is False
    with pytest.raises(RuntimeError, match="not in production"):
        assert_approved("hyp_sma200_long")
