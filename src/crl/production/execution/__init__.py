"""Live/paper execution — not implemented in Phase 1.

Any future implementation must:
- refuse to run unless PHASE1_EXECUTION_ENABLED is lifted by a later phase flag
- enforce risk.constraints with no agent override path
- use only strategies in production.strategies.APPROVED
"""


def place_order(*_args, **_kwargs):  # noqa: ANN001
    raise RuntimeError(
        "Execution is disabled in Phase 1 (research-only). "
        "No orders will be placed."
    )
