"""LEDA — Layered Evidence Decision Architecture.

Layers: Forecast → Risk → Portfolio → Execution, fed by calibrated evidence channels.
See docs/ARCHITECTURE_LAYERED_DECISION_STACK.md and docs/RESEARCH_ROADMAP_LEDA_V1.md.
"""

from crl.leda.stack import decide_bar
from crl.leda.types import EvidenceRecord, EvidenceSink, LayerName

__all__ = ["EvidenceRecord", "EvidenceSink", "LayerName", "decide_bar"]
