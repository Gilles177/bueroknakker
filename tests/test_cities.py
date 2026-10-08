from pathlib import Path

import yaml

from src.models import Step

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

# Must match the CITIES list in app.py
CITIES = ["Berlin", "Munich", "Hamburg", "Cologne"]


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
    assert len(steps) >= 10
    ids = [s.id for s in steps]
    assert len(ids) == len(set(ids)), "duplicate step ids"
