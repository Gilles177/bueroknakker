from datetime import date

from src.engine import resolve_steps, step_applies
from src.models import AppliesTo, Step, UserProfile


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
    step = make_step(
        applies_to=AppliesTo(status=["Freelancer"], city=["Berlin"])
    )
    assert step_applies(step, make_profile(status="Freelancer", city="Berlin"))
    assert not step_applies(
        step, make_profile(status="Freelancer", city="Munich")
    )
    assert not step_applies(step, make_profile(status="EU citizen", city="Berlin"))


def test_no_filters_means_no_match():
    step = make_step(applies_to=AppliesTo())
    assert not step_applies(step, make_profile())


def test_deadline_and_sorting():
    s_late = make_step(
        id="late", applies_to=AppliesTo(all=True), deadline_days=30
    )
    s_early = make_step(
        id="early", applies_to=AppliesTo(all=True), deadline_days=7
    )
    s_none = make_step(id="none", applies_to=AppliesTo(all=True))

    resolved = resolve_steps(
        [s_late, s_early, s_none],
        make_profile(),
        today=date(2025, 1, 1),
    )
    ids = [r.step.id for r in resolved]
    assert ids == ["early", "late", "none"]
    assert resolved[0].deadline == date(2025, 1, 8)
    assert resolved[2].deadline is None
