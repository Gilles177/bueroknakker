from __future__ import annotations

from datetime import date, timedelta
from typing import Iterable, List

from .models import ResolvedStep, Step, UserProfile


def step_applies(step: Step, profile: UserProfile) -> bool:
    a = step.applies_to
    if a.all:
        return True

    # Step has no filters at all -> do not apply (safer default).
    if not a.status and not a.city and a.family is None:
        return False

    if a.status and profile.status not in a.status:
        return False
    if a.city and profile.city not in a.city:
        return False
    if a.family is not None and a.family != profile.family:
        return False
    return True


def resolve_steps(
    steps: Iterable[Step],
    profile: UserProfile,
    today: date | None = None,
) -> List[ResolvedStep]:
    today = today or date.today()
    out: List[ResolvedStep] = []
    for s in steps:
        if not step_applies(s, profile):
            continue
        deadline = None
        days_left = None
        if s.deadline_days is not None:
            deadline = profile.arrival_date + timedelta(days=s.deadline_days)
            days_left = (deadline - today).days
        out.append(ResolvedStep(step=s, deadline=deadline, days_left=days_left))

    # Steps with a deadline first, sorted by deadline; undated steps last.
    out.sort(key=lambda r: (r.deadline is None, r.deadline or date.max, r.step.id))
    return out
