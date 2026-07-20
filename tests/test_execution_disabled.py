import pytest

from crl.production.execution import place_order
from crl.production import PHASE1_EXECUTION_ENABLED


def test_execution_disabled():
    assert PHASE1_EXECUTION_ENABLED is False
    with pytest.raises(RuntimeError):
        place_order(symbol="BTCUSDT", side="buy", qty=1)
