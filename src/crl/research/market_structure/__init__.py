"""Market-structure research (H1). Hedged styles research-only unless LIVE authorized."""

from crl.research.market_structure.funding_carry import (
    CarryRule,
    run_funding_carry_backtest,
)

__all__ = ["CarryRule", "run_funding_carry_backtest"]
