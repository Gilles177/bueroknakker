from __future__ import annotations

from datetime import date
from typing import Optional

UMLAUT_MAP = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "ae", "Ö": "oe", "Ü": "ue",
})


def slug(text: str) -> str:
    """ASCII-safe filename slug. Düsseldorf -> duesseldorf."""
    return text.lower().translate(UMLAUT_MAP)


def format_eur(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"{value:,.0f} €".replace(",", " ")


def format_date(d: Optional[date]) -> str:
    if d is None:
        return "—"
    return d.strftime("%d.%m.%Y")


def days_label(days_left: Optional[int], lang: str = "en") -> str:
    if days_left is None:
        return ""
    if days_left < 0:
        n = abs(days_left)
        return f"{n} Tage überfällig" if lang == "de" else f"{n} days overdue"
    if days_left == 0:
        return "Heute fällig" if lang == "de" else "Due today"
    unit = "Tage" if lang == "de" else "days"
    return f"{days_left} {unit}"


def urgency_color(days_left: Optional[int]) -> str:
    if days_left is None:
        return "#64748b"
    if days_left < 0:
        return "#dc2626"
    if days_left <= 7:
        return "#f59e0b"
    if days_left <= 30:
        return "#3b82f6"
    return "#10b981"


def urgency_label(days_left: Optional[int], lang: str = "en") -> str:
    if days_left is None:
        return "—"
    if days_left < 0:
        return "Überfällig" if lang == "de" else "Overdue"
    if days_left <= 7:
        return "Dringend" if lang == "de" else "Urgent"
    if days_left <= 30:
        return "Bald" if lang == "de" else "Soon"
    return "Im Plan" if lang == "de" else "On track"
