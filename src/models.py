from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class StepCategory(str, Enum):
    REGISTRATION = "registration"
    TAX = "tax"
    HEALTH = "health"
    FINANCE = "finance"
    IMMIGRATION = "immigration"
    WORK = "work"
    FAMILY = "family"
    HOUSING = "housing"
    TRANSPORT = "transport"
    OTHER = "other"


class Difficulty(int, Enum):
    EASY = 1
    MEDIUM = 2
    HARD = 3
    VERY_HARD = 4
    NIGHTMARE = 5


class Channel(str, Enum):
    ONLINE = "online"
    IN_PERSON = "in_person"
    MAIL = "mail"
    PHONE = "phone"
    MIXED = "mixed"


class AppliesTo(BaseModel):
    """Semantics: OR within a list, AND across categories.

    - all=True overrides everything → applies to everyone.
    - Within status, city, etc.: ANY match is enough.
    - Across categories: ALL must match.
    - family=None means "don't care"; True/False means "must equal".
    """

    all: bool = False
    status: List[str] = Field(default_factory=list)
    city: List[str] = Field(default_factory=list)
    family: Optional[bool] = None
    has_children: Optional[bool] = None
    move_reason: List[str] = Field(default_factory=list)
    contract_type: List[str] = Field(default_factory=list)


class GermanPhrase(BaseModel):
    context_de: str
    phrase_de: str
    phrase_en: str


class Step(BaseModel):
    id: str
    title_de: str
    title_en: str
    category: StepCategory = StepCategory.OTHER
    description_de: str = ""
    description_en: str = ""

    applies_to: AppliesTo = Field(default_factory=AppliesTo)

    # Timing
    deadline_days: Optional[int] = None
    duration_days: Optional[int] = None

    # Cost (EUR)
    cost_eur_min: Optional[float] = None
    cost_eur_max: Optional[float] = None

    # Metadata
    difficulty: Difficulty = Difficulty.MEDIUM
    priority: int = 3  # 1–5
    channel: Channel = Channel.MIXED

    # DAG
    depends_on: List[str] = Field(default_factory=list)

    # Content
    documents: List[str] = Field(default_factory=list)
    tips_de: List[str] = Field(default_factory=list)
    tips_en: List[str] = Field(default_factory=list)
    phrases: List[GermanPhrase] = Field(default_factory=list)

    # Links
    link: Optional[str] = None
    link_by_city: Dict[str, str] = Field(default_factory=dict)
    source_urls: List[str] = Field(default_factory=list)

    # Notes
    notes_de: str = ""
    notes_en: str = ""


class FamilyMember(BaseModel):
    name: str
    relation: str  # "self", "spouse", "child", "other"
    age: Optional[int] = None
    nationality: str = ""


class UserProfile(BaseModel):
    city: str
    status: str
    arrival_date: date
    move_reason: str = "work"
    family: bool = False
    members: List[FamilyMember] = Field(default_factory=list)
    contract_type: str = "employee"
    language: str = "en"

    @property
    def has_children(self) -> bool:
        return any(m.relation == "child" for m in self.members)


class ResolvedStep(BaseModel):
    step: Step
    deadline: Optional[date] = None
    days_left: Optional[int] = None
    blocked_by: List[str] = Field(default_factory=list)
    depth: int = 0


class ActionPlan(BaseModel):
    profile: UserProfile
    steps: List[ResolvedStep]
    by_id: Dict[str, ResolvedStep]

    topological_order: List[str] = Field(default_factory=list)
    levels: Dict[str, int] = Field(default_factory=dict)
    critical_path: List[str] = Field(default_factory=list)

    total_steps: int = 0
    total_cost_min: float = 0.0
    total_cost_max: float = 0.0
    total_duration_days: int = 0
    earliest_finish: Optional[date] = None

    ready_now: List[str] = Field(default_factory=list)
    blocked: List[str] = Field(default_factory=list)
