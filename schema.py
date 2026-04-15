"""
schema.py — Shared data structures for the Requirements Crew.
Every agent reads and writes these structures.
Future crews import from here too — don't change field names once stable.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Story:
    """Input story. Paste as many fields as you have — only title + description required."""
    story_id: str
    title: str
    description: str
    acceptance_criteria: List[str] = field(default_factory=list)
    story_points: Optional[int] = None
    sprint: Optional[str] = None

    def to_text(self) -> str:
        """Render story as plain text for LLM prompts."""
        parts = [
            f"Story ID   : {self.story_id}",
            f"Title      : {self.title}",
            f"Description: {self.description}",
        ]
        if self.acceptance_criteria:
            parts.append("Acceptance Criteria:")
            for ac in self.acceptance_criteria:
                parts.append(f"  - {ac}")
        if self.story_points:
            parts.append(f"Story Points: {self.story_points}")
        if self.sprint:
            parts.append(f"Sprint: {self.sprint}")
        return "\n".join(parts)

    def to_short_text(self, max_description_chars: int = 600, max_ac_items: int = 5) -> str:
        """Render a compact story summary for follow-up tasks."""
        def truncate(value: str, limit: int) -> str:
            return value if len(value) <= limit else value[: limit - 1] + "…"

        description = truncate(self.description, max_description_chars)
        parts = [
            f"Story ID   : {self.story_id}",
            f"Title      : {self.title}",
            f"Description: {description}",
        ]

        if self.acceptance_criteria:
            parts.append("Acceptance Criteria:")
            for ac in self.acceptance_criteria[:max_ac_items]:
                parts.append(f"  - {truncate(ac, 200)}")
            if len(self.acceptance_criteria) > max_ac_items:
                parts.append(f"  - ...and {len(self.acceptance_criteria) - max_ac_items} more acceptance criteria")

        if self.story_points:
            parts.append(f"Story Points: {self.story_points}")
        if self.sprint:
            parts.append(f"Sprint: {self.sprint}")
        return "\n".join(parts)


@dataclass
class AmbiguityIssue:
    type: str           # VAGUE_QUALIFIER | UNDEFINED_ACTOR | MISSING_AC |
                        # MISSING_ERROR_PATH | BOUNDARY_MISSING | UNCLEAR_OWNERSHIP
    phrase: str
    explanation: str
    suggested_rewrite: str


@dataclass
class AmbiguityReport:
    story_id: str
    ambiguity_score: int        # 0-100, higher = more ambiguous
    overall_risk: str           # HIGH | MEDIUM | LOW
    issues: List[AmbiguityIssue] = field(default_factory=list)
    testable_conditions_missing: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class Risk:
    category: str       # DELIVERY | TECHNICAL | BUSINESS
    description: str
    likelihood: str     # HIGH | MEDIUM | LOW
    impact: str         # HIGH | MEDIUM | LOW
    mitigation: str


@dataclass
class RiskReport:
    story_id: str
    overall_risk_level: str     # HIGH | MEDIUM | LOW
    risks: List[Risk] = field(default_factory=list)
    dependencies_identified: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class DorBlocker:
    criterion: str
    status: str         # MISSING | PARTIAL | UNCLEAR
    what_is_needed: str


@dataclass
class DorReport:
    story_id: str
    dor_status: str             # READY | NOT_READY | CONDITIONALLY_READY
    readiness_score: int        # 0-100
    blockers: List[DorBlocker] = field(default_factory=list)
    conditions_to_proceed: List[str] = field(default_factory=list)
    recommendation: str = ""


@dataclass
class StoryReadinessReport:
    """Final consolidated output per story — what the TPM sees."""
    story_id: str
    title: str
    dor_status: str
    readiness_score: int
    overall_risk_level: str
    ambiguity_score: int
    key_blockers: List[str] = field(default_factory=list)
    key_risks: List[str] = field(default_factory=list)
    immediate_actions: List[str] = field(default_factory=list)
    tpm_summary: str = ""