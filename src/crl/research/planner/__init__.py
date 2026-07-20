"""Evidence-driven research planner — maximise knowledge per experiment.

Not a trading module. Does not weaken gates or place orders.
"""

from crl.research.planner.plan import ResearchPlan, build_research_plan, update_knowledge_after_batch
from crl.research.planner.thesis_tree import rebuild_thesis_tree, record_experiment_on_tree

__all__ = [
    "ResearchPlan",
    "build_research_plan",
    "update_knowledge_after_batch",
    "rebuild_thesis_tree",
    "record_experiment_on_tree",
]
