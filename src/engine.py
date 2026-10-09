from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional

from .models import (
    ActionPlan,
    ResolvedStep,
    Step,
    UserProfile,
)


# ---------------------------------------------------------------- matching

def step_applies(step: Step, profile: UserProfile) -> bool:
    a = step.applies_to
    if a.all:
        return True

    if not (
        a.status or a.city or a.family is not None
        or a.has_children is not None or a.move_reason or a.contract_type
    ):
        return False

    if a.status and profile.status not in a.status:
        return False
    if a.city and profile.city not in a.city:
        return False
    if a.family is not None and a.family != profile.family:
        return False
    if a.has_children is not None and a.has_children != profile.has_children:
        return False
    if a.move_reason and profile.move_reason not in a.move_reason:
        return False
    if a.contract_type and profile.contract_type not in a.contract_type:
        return False
    return True


def resolve_link(step: Step, city: str) -> Optional[str]:
    return step.link_by_city.get(city) or step.link


# ---------------------------------------------------------------- DAG

def _applicable_ids(steps: Iterable[Step], profile: UserProfile) -> set[str]:
    return {s.id for s in steps if step_applies(s, profile)}


def _deps(step: Step, applicable: set[str]) -> List[str]:
    return [d for d in step.depends_on if d in applicable]


def _topological_order(
    steps_by_id: Dict[str, Step], applicable: set[str]
) -> List[str]:
    in_degree: Dict[str, int] = {sid: 0 for sid in applicable}
    successors: Dict[str, List[str]] = {sid: [] for sid in applicable}

    for sid in applicable:
        for dep in _deps(steps_by_id[sid], applicable):
            in_degree[sid] += 1
            successors[dep].append(sid)

    queue = sorted(sid for sid, deg in in_degree.items() if deg == 0)
    order: List[str] = []

    while queue:
        sid = queue.pop(0)
        order.append(sid)
        for succ in successors[sid]:
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)
        queue.sort()

    if len(order) != len(applicable):
        # cycle → degrade gracefully rather than crash
        return sorted(applicable)
    return order


def _compute_levels(
    steps_by_id: Dict[str, Step], applicable: set[str], topo: List[str]
) -> Dict[str, int]:
    levels: Dict[str, int] = {}
    for sid in topo:
        deps = [d for d in _deps(steps_by_id[sid], applicable) if d in levels]
        levels[sid] = 0 if not deps else max(levels[d] for d in deps) + 1
    return levels


def _compute_critical_path(
    steps_by_id: Dict[str, Step], applicable: set[str], topo: List[str]
) -> tuple[List[str], int]:
    dist: Dict[str, int] = {}
    parent: Dict[str, Optional[str]] = {}

    for sid in topo:
        weight = steps_by_id[sid].duration_days or 1
        deps = [d for d in _deps(steps_by_id[sid], applicable) if d in dist]
        if not deps:
            dist[sid] = weight
            parent[sid] = None
        else:
            best = max(deps, key=lambda d: dist[d])
            dist[sid] = dist[best] + weight
            parent[sid] = best

    if not dist:
        return [], 0

    end = max(dist, key=lambda s: dist[s])
    path: List[str] = []
    cur: Optional[str] = end
    while cur is not None:
        path.append(cur)
        cur = parent[cur]
    return list(reversed(path)), dist[end]


# ---------------------------------------------------------------- public API

def build_plan(
    steps: Iterable[Step],
    profile: UserProfile,
    today: Optional[date] = None,
) -> ActionPlan:
    today = today or date.today()
    all_steps = list(steps)
    applicable = _applicable_ids(all_steps, profile)
    steps_by_id = {s.id: s for s in all_steps}

    topo = _topological_order(steps_by_id, applicable)
    levels = _compute_levels(steps_by_id, applicable, topo)
    critical, total_duration = _compute_critical_path(steps_by_id, applicable, topo)

    resolved: List[ResolvedStep] = []
    by_id: Dict[str, ResolvedStep] = {}

    for sid in topo:
        s = steps_by_id[sid]
        deadline = None
        days_left = None
        if s.deadline_days is not None:
            deadline = profile.arrival_date + timedelta(days=s.deadline_days)
            days_left = (deadline - today).days

        r = ResolvedStep(
            step=s,
            deadline=deadline,
            days_left=days_left,
            blocked_by=_deps(s, applicable),
            depth=levels.get(sid, 0),
        )
        resolved.append(r)
        by_id[sid] = r

    resolved.sort(
        key=lambda r: (
            r.deadline is None,
            r.deadline or date.max,
            r.depth,
            r.step.id,
        )
    )

    cost_min = sum((r.step.cost_eur_min or 0) for r in resolved)
    cost_max = sum((r.step.cost_eur_max or 0) for r in resolved)

    duration = max(
        (levels[sid] + (steps_by_id[sid].duration_days or 1) for sid in applicable),
        default=0,
    )
    earliest_finish = (
        profile.arrival_date + timedelta(days=total_duration)
        if total_duration
        else None
    )

    ready = [sid for sid in topo if not by_id[sid].blocked_by]
    blocked = [sid for sid in topo if by_id[sid].blocked_by]

    return ActionPlan(
        profile=profile,
        steps=resolved,
        by_id=by_id,
        topological_order=topo,
        levels=levels,
        critical_path=critical,
        total_steps=len(resolved),
        total_cost_min=cost_min,
        total_cost_max=cost_max,
        total_duration_days=total_duration,
        earliest_finish=earliest_finish,
        ready_now=ready,
        blocked=blocked,
    )


def resolve_steps(
    steps: Iterable[Step],
    profile: UserProfile,
    today: Optional[date] = None,
) -> List[ResolvedStep]:
    """Backwards-compatible wrapper used by app.py and export.py."""
    return build_plan(steps, profile, today).steps
