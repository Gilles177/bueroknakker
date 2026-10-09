from __future__ import annotations

from datetime import date

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from src.engine import build_plan
from src.models import AppliesTo, Step, UserProfile


CITIES = ["Berlin", "Munich", "Hamburg", "Cologne"]
STATUSES = ["EU citizen", "Non-EU student", "Non-EU employee", "Freelancer"]
REASONS = ["work", "study", "family", "other"]
CONTRACTS = ["employee", "student", "freelancer", "unemployed"]


def make_step(i: int, *, depends_on=None, **kwargs) -> Step:
    return Step(
        id=f"s{i}",
        title_de=f"S{i}",
        title_en=f"S{i}",
        applies_to=kwargs.pop("applies_to", AppliesTo(all=True)),
        depends_on=depends_on or [],
        **kwargs,
    )


@st.composite
def profiles(draw) -> UserProfile:
    return UserProfile(
        city=draw(st.sampled_from(CITIES)),
        status=draw(st.sampled_from(STATUSES)),
        arrival_date=draw(
            st.dates(min_value=date(2020, 1, 1), max_value=date(2030, 1, 1))
        ),
        move_reason=draw(st.sampled_from(REASONS)),
        contract_type=draw(st.sampled_from(CONTRACTS)),
        family=draw(st.booleans()),
    )


@given(profile=profiles())
@settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_plan_contains_exactly_applicable_steps(profile: UserProfile):
    steps = [make_step(i, applies_to=AppliesTo(all=True)) for i in range(5)]
    plan = build_plan(steps, profile)
    assert plan.total_steps == 5


@given(profile=profiles())
@settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_topological_order_has_no_forward_references(profile: UserProfile):
    a = make_step(0)
    b = make_step(1, depends_on=["s0"])
    c = make_step(2, depends_on=["s1"])
    d = make_step(3, depends_on=["s1"])
    plan = build_plan([a, b, c, d], profile)

    position = {sid: i for i, sid in enumerate(plan.topological_order)}
    for sid in plan.topological_order:
        for dep in plan.by_id[sid].blocked_by:
            assert position[dep] < position[sid], f"{dep} must come before {sid}"


@given(profile=profiles())
@settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_costs_sum_consistently(profile: UserProfile):
    a = make_step(0, cost_eur_min=10, cost_eur_max=20)
    b = make_step(1, cost_eur_min=5, cost_eur_max=15)
    c = make_step(2)
    plan = build_plan([a, b, c], profile)
    assert plan.total_cost_min == 15
    assert plan.total_cost_max == 35
    assert plan.total_cost_min <= plan.total_cost_max


@given(profile=profiles())
@settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_critical_path_is_an_ordered_chain(profile: UserProfile):
    a = make_step(0, duration_days=2)
    b = make_step(1, duration_days=3, depends_on=["s0"])
    c = make_step(2, duration_days=5, depends_on=["s1"])
    plan = build_plan([a, b, c], profile)
    assert plan.critical_path == ["s0", "s1", "s2"]
    assert plan.total_duration_days == 10


@given(profile=profiles())
@settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_ready_and_blocked_partition_the_plan(profile: UserProfile):
    a = make_step(0)
    b = make_step(1, depends_on=["s0"])
    plan = build_plan([a, b], profile)
    all_ids = set(plan.topological_order)
    assert set(plan.ready_now).isdisjoint(plan.blocked)
    assert set(plan.ready_now) | set(plan.blocked) == all_ids


@given(profile=profiles())
@settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_empty_step_list_yields_empty_plan(profile: UserProfile):
    plan = build_plan([], profile)
    assert plan.total_steps == 0
    assert plan.total_cost_min == 0
    assert plan.total_duration_days == 0
    assert plan.critical_path == []


@given(profile=profiles())
@settings(max_examples=80, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_cycle_does_not_crash(profile: UserProfile):
    a = make_step(0, depends_on=["s1"])
    b = make_step(1, depends_on=["s0"])
    plan = build_plan([a, b], profile)
    assert set(plan.topological_order) == {"s0", "s1"}
