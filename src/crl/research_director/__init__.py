"""Research Director — principal investigator of the laboratory.

Coordinates programmes and knowledge; does not run experiments for their own sake
and never weakens scientific gates.
"""

from crl.research_director.core import (
    composite_score,
    director_report,
    knowledge_graph_summary,
    list_programmes,
    ranked_directions,
    sync_rd_state,
)
from crl.research_director.inefficiency import (
    eir_required,
    inefficiency_report,
    ranked_inefficiencies,
    top_inefficiency,
)
from crl.research_director.phase1 import (
    phase1_status,
    record_phase1_event,
    refuse_new_programme,
    set_phase1_conclusion,
)

__all__ = [
    "composite_score",
    "director_report",
    "knowledge_graph_summary",
    "list_programmes",
    "ranked_directions",
    "sync_rd_state",
    "inefficiency_report",
    "ranked_inefficiencies",
    "top_inefficiency",
    "eir_required",
    "phase1_status",
    "set_phase1_conclusion",
    "record_phase1_event",
    "refuse_new_programme",
]
