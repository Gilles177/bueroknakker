from pathlib import Path

import yaml

from src.models import Step

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

CITIES = [
    "Berlin",
    "Munich",
    "Hamburg",
    "Cologne",
    "Frankfurt",
    "Stuttgart",
    "Düsseldorf",
    "Leipzig",
    "Dresden",
    "Nuremberg",
    "Hannover",
    "Bremen",
]


def test_every_city_has_a_yaml():
    for city in CITIES:
        path = DATA / "cities" / f"{city.lower()}.yaml"
        assert path.exists(), f"missing city file: {path}"


def test_city_yaml_schema():
    for city in CITIES:
        path = DATA / "cities" / f"{city.lower()}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert data.get("name") == city


def test_steps_yaml_loads_as_models():
    raw = yaml.safe_load((DATA / "steps.yaml").read_text(encoding="utf-8"))
    steps = [Step(**s) for s in raw]
    assert len(steps) >= 40
    ids = [s.id for s in steps]
    assert len(ids) == len(set(ids)), "duplicate step ids"


def test_step_link_by_city_keys_are_known_cities():
    raw = yaml.safe_load((DATA / "steps.yaml").read_text(encoding="utf-8"))
    steps = [Step(**s) for s in raw]
    known = set(CITIES)
    for step in steps:
        for city in step.link_by_city.keys():
            assert city in known, f"step {step.id}: unknown city {city}"


def test_step_dependencies_reference_existing_ids():
    raw = yaml.safe_load((DATA / "steps.yaml").read_text(encoding="utf-8"))
    steps = [Step(**s) for s in raw]
    ids = {s.id for s in steps}
    for step in steps:
        for dep in step.depends_on:
            assert dep in ids, f"step {step.id}: unknown dependency {dep}"
