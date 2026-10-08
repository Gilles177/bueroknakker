from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


class AppliesTo(BaseModel):
    """Filters that decide who a step applies to.

    Semantics:
      - If `all` is True, the step applies to everyone.
      - Otherwise, each non-empty filter must match (AND across categories),
        and within a category any match is enough (OR within a list).
    """

    all: bool = False
    status: List[str] = Field(default_factory=list)
    city: List[str] = Field(default_factory=list)
    family: Optional[bool] = None


class Step(BaseModel):
    id: str
    title_de: str
    title_en: str
    description_de: str = ""
    description_en: str = ""
    applies_to: AppliesTo = Field(default_factory=AppliesTo)
    deadline_days: Optional[int] = None
    documents: List[str] = Field(default_factory=list)
    link: Optional[str] = None
    notes_de: str = ""
    notes_en: str = ""
    cost_eur: Optional[float] = None


class UserProfile(BaseModel):
    city: str
    status: str
    arrival_date: date
    family: bool = False
    language: str = "en"


class ResolvedStep(BaseModel):
    step: Step
    deadline: Optional[date] = None
    days_left: Optional[int] = None
