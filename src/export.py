from __future__ import annotations

from datetime import datetime
from typing import Iterable

from fpdf import FPDF

from .models import ResolvedStep, UserProfile


def steps_to_pdf(
    resolved: Iterable[ResolvedStep],
    profile: UserProfile,
    lang: str = "en",
) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("helvetica", "B", 20)
    pdf.cell(0, 12, "BüroKnakker", ln=True)
    pdf.set_font("helvetica", "", 11)
    pdf.cell(0, 6, "Germany bureaucracy, cracked.", ln=True)
    pdf.ln(4)

    pdf.set_font("helvetica", "", 10)
    pdf.cell(0, 5, f"City: {profile.city}", ln=True)
    pdf.cell(0, 5, f"Status: {profile.status}", ln=True)
    pdf.cell(0, 5, f"Arrival: {profile.arrival_date.strftime('%d.%m.%Y')}", ln=True)
    pdf.cell(0, 5, f"Family: {'yes' if profile.family else 'no'}", ln=True)
    pdf.ln(6)

    for r in resolved:
        s = r.step
        pdf.set_font("helvetica", "B", 12)
        title = s.title_en if lang == "en" else s.title_de
        pdf.multi_cell(0, 6, title)
        pdf.set_font("helvetica", "", 10)

        if r.deadline:
            pdf.cell(0, 5, f"Deadline: {r.deadline.strftime('%d.%m.%Y')}", ln=True)

        notes = s.notes_en if lang == "en" else s.notes_de
        if notes:
            pdf.multi_cell(0, 5, notes)

        for doc in s.documents:
            pdf.cell(0, 5, f"  [ ] {doc}", ln=True)

        if s.link:
            pdf.set_text_color(0, 80, 180)
            pdf.multi_cell(0, 5, s.link)
            pdf.set_text_color(0, 0, 0)

        pdf.ln(3)

    return bytes(pdf.output())


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
