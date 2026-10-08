from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from .engine import resolve_link
from .models import ResolvedStep, UserProfile

# ---------------------------------------------------------------- fonts

FONT_DIR = Path(__file__).parent / "fonts"
FONT_REGULAR = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"

# Reset cursor to left margin and move to next line after every multi_cell.
NR = {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}


def _ensure_fonts() -> None:
    missing = [str(p) for p in (FONT_REGULAR, FONT_BOLD) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing font files: " + ", ".join(missing)
            + ". Put DejaVuSans.ttf and DejaVuSans-Bold.ttf in src/fonts/."
        )


# ---------------------------------------------------------------- pdf


def steps_to_pdf(
    resolved: Iterable[ResolvedStep],
    profile: UserProfile,
    lang: str = "en",
) -> bytes:
    _ensure_fonts()

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=15, top=15, right=15)

    pdf.add_font("DejaVu", "", str(FONT_REGULAR))
    pdf.add_font("DejaVu", "B", str(FONT_BOLD))

    pdf.add_page()

    W = pdf.epw  # effective page width with the 15mm margins

    # Header
    pdf.set_font("DejaVu", "B", 20)
    pdf.multi_cell(W, 10, "BüroKnakker", **NR)
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(W, 6, "Germany bureaucracy, cracked.", **NR)
    pdf.ln(3)

    # Profile block
    pdf.set_font("DejaVu", "", 10)
    pdf.multi_cell(W, 5, f"City: {profile.city}", **NR)
    pdf.multi_cell(W, 5, f"Status: {profile.status}", **NR)
    pdf.multi_cell(W, 5, f"Arrival: {profile.arrival_date.strftime('%d.%m.%Y')}", **NR)
    pdf.multi_cell(W, 5, f"Family: {'yes' if profile.family else 'no'}", **NR)
    pdf.ln(4)

    # Steps
    for r in resolved:
        s = r.step

        pdf.set_font("DejaVu", "B", 12)
        title = s.title_en if lang == "en" else s.title_de
        pdf.multi_cell(W, 6, title, **NR)

        pdf.set_font("DejaVu", "", 10)

        if r.deadline:
            pdf.multi_cell(W, 5, f"Deadline: {r.deadline.strftime('%d.%m.%Y')}", **NR)

        notes = s.notes_en if lang == "en" else s.notes_de
        if notes:
            pdf.multi_cell(W, 5, notes, **NR)

        for doc in s.documents:
            pdf.multi_cell(W, 5, f"  [ ] {doc}", **NR)

        url = resolve_link(s, profile.city)
        if url:
            pdf.set_text_color(0, 80, 180)
            pdf.multi_cell(W, 5, url, **NR)
            pdf.set_text_color(0, 0, 0)

        pdf.ln(3)

    return bytes(pdf.output())


# ---------------------------------------------------------------- ics


def steps_to_ics(resolved: Iterable[ResolvedStep], profile: UserProfile) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//BuroKnakker//EN",
        "CALSCALE:GREGORIAN",
    ]
    now = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for r in resolved:
        if r.deadline is None:
            continue
        s = r.step
        d = r.deadline.strftime("%Y%m%d")
        desc = (s.notes_en or s.notes_de).replace("\n", " ")

        lines += [
            "BEGIN:VEVENT",
            f"UID:{s.id}-{d}@bueroknakker.local",
            f"DTSTAMP:{now}",
            f"DTSTART;VALUE=DATE:{d}",
            f"DTEND;VALUE=DATE:{d}",
            f"SUMMARY:{s.title_en} / {s.title_de}",
            f"DESCRIPTION:{desc}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
