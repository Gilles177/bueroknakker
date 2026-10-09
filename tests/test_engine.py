from datetime import date

from src.engine import build_plan, resolve_link, resolve_steps, step_applies
from src.models import AppliesTo, FamilyMember, Step, UserProfile


def make_step(**kwargs) -> Step:
    base = dict(id="x", title_de="X", title_en="X")
    base.update(kwargs)
    return Step(**base)


def make_profile(**kwargs) -> UserProfile:
    base = dict(
        city="Berlin",
        status="EU citizen",
        arrival_date=date(2025, 1, 1),
        family=False,
    )
    base.update(kwargs)
    return UserProfile(**base)


# ---------------------------------------------------------------- matching

def test_all_applies_to_everyone():
    step = make_step(applies_to=AppliesTo(all=True))
    assert step_applies(step, make_profile())


def test_status_filter():
    step = make_step(applies_to=AppliesTo(status=["Non-EU student"]))
    assert step_applies(step, make_profile(status="Non-EU student"))
    assert not step_applies(step, make_profile(status="EU citizen"))


def test_family_filter():
    step = make_step(applies_to=AppliesTo(family=True))
    assert step_applies(step, make_profile(family=True))
    assert not step_applies(step, make_profile(family=False))


def test_city_and_status_are_anded():
    step = make_step(applies_to=AppliesTo(status=["Freelancer"], city=["Berlin"]))
    assert step_applies(step, make_profile(status="Freelancer", city="Berlin"))
    assert not step_applies(step, make_profile(status="Freelancer", city="Munich"))
    assert not step_applies(step, make_profile(status="EU citizen", city="Berlin"))


def test_no_filters_means_no_match():
    step = make_step(applies_to=AppliesTo())
    assert not step_applies(step, make_profile())


def test_has_children_filter():
    step = make_step(applies_to=AppliesTo(has_children=True))
    assert not step_applies(step, make_profile())
    with_kid = make_profile(
        family=True,
        members=[FamilyMember(name="Kid", relation="child", age=4)],
    )
    assert step_applies(step, with_kid)


# ---------------------------------------------------------------- links

def test_resolve_link_prefers_city_specific():
    step = make_step(
        link="https://example.com/generic",
        link_by_city={"Berlin": "https://example.com/berlin"},
    )
    assert resolve_link(step, "Berlin") == "https://example.com/berlin"
    assert resolve_link(step, "Hamburg") == "https://example.com/generic"


def test_resolve_link_no_fallback_returns_none():
    step = make_step(link=None, link_by_city={"Berlin": "https://example.com/berlin"})
    assert resolve_link(step, "Munich") is None


# ---------------------------------------------------------------- plan

def test_deadline_and_sorting():
    late = make_step(id="late", applies_to=AppliesTo(all=True), deadline_days=30)
    early = make_step(id="early", applies_to=AppliesTo(all=True), deadline_days=7)
    none = make_step(id="none", applies_to=AppliesTo(all=True))

    resolved = resolve_steps([late, early, none], make_profile(), today=date(2025, 1, 1))
    ids = [r.step.id for r in resolved]
    assert ids == ["early", "late", "none"]
    assert resolved[0].deadline == date(2025, 1, 8)
    assert resolved[2].deadline is None


def test_topological_order_respects_dependencies():
    a = make_step(id="a", applies_to=AppliesTo(all=True))
    b = make_step(id="b", applies_to=AppliesTo(all=True), depends_on=["a"])
    c = make_step(id="c", applies_to=AppliesTo(all=True), depends_on=["b"])

    plan = build_plan([c, a, b], make_profile())
    assert plan.topological_order == ["a", "b", "c"]


def test_blocked_and_ready():
    a = make_step(id="a", applies_to=AppliesTo(all=True))
    b = make_step(id="b", applies_to=AppliesTo(all=True), depends_on=["a"])

    plan = build_plan([a, b], make_profile())
    assert plan.ready_now == ["a"]
    assert plan.blocked == ["b"]
    assert plan.by_id["b"].blocked_by == ["a"]


def test_levels_parallel_groups():
    a = make_step(id="a", applies_to=AppliesTo(all=True))
    b = make_step(id="b", applies_to=AppliesTo(all=True))
    c = make_step(id="c", applies_to=AppliesTo(all=True), depends_on=["a", "b"])

    plan = build_plan([a, b, c], make_profile())
    assert plan.levels["a"] == 0
    assert plan.levels["b"] == 0
    assert plan.levels["c"] == 1


def test_critical_path():
    a = make_step(id="a", applies_to=AppliesTo(all=True), duration_days=2)
    b = make_step(id="b", applies_to=AppliesTo(all=True), depends_on=["a"], duration_days=3)
    c = make_step(id="c", applies_to=AppliesTo(all=True), depends_on=["b"], duration_days=1)
    d = make_step(id="d", applies_to=AppliesTo(all=True), depends_on=["a"], duration_days=1)

    plan = build_plan([a, b, c, d], make_profile())
    assert plan.critical_path == ["a", "b", "c"]
    assert plan.total_duration_days == 6


def test_costs_summed():
    a = make_step(id="a", applies_to=AppliesTo(all=True), cost_eur_min=10, cost_eur_max=20)
    b = make_step(id="b", applies_to=AppliesTo(all=True), cost_eur_min=5, cost_eur_max=15)

    plan = build_plan([a, b], make_profile())
    assert plan.total_cost_min == 15
    assert plan.total_cost_max == 35


def test_cycle_falls_back_safely():
    a = make_step(id="a", applies_to=AppliesTo(all=True), depends_on=["b"])
    b = make_step(id="b", applies_to=AppliesTo(all=True), depends_on=["a"])

    plan = build_plan([a, b], make_profile())
    assert set(plan.topological_order) == {"a", "b"}
