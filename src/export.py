from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable, Optional

from fpdf import FPDF
from fpdf.enums import XPos, YPos

from .models import ActionPlan, ResolvedStep, UserProfile

FONT_DIR = Path(__file__).parent / "fonts"
FONT_REGULAR = FONT_DIR / "DejaVuSans.ttf"
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"

NR = {"new_x": XPos.LMARGIN, "new_y": YPos.NEXT}

CATEGORY_COLORS_HEX = {
    "registration": (59, 130, 246),
    "tax":          (139, 92, 246),
    "health":       (16, 185, 129),
    "finance":      (245, 158, 11),
    "immigration":  (239, 68, 68),
    "work":         (6, 182, 212),
    "family":       (236, 72, 153),
    "housing":      (132, 204, 22),
    "transport":    (99, 102, 241),
    "other":        (100, 116, 139),
}

CATEGORY_LABELS = {
    "registration": ("Registration", "Anmeldung"),
    "tax":          ("Tax", "Steuern"),
    "health":       ("Health", "Gesundheit"),
    "finance":      ("Finance", "Finanzen"),
    "immigration":  ("Immigration", "Aufenthalt"),
    "work":         ("Work", "Arbeit"),
    "family":       ("Family", "Familie"),
    "housing":      ("Housing", "Wohnen"),
    "transport":    ("Transport", "Verkehr"),
    "other":        ("Other", "Sonstiges"),
}

DIFFICULTY_LABELS = {
    1: ("Trivial", "Trivial"),
    2: ("Easy", "Einfach"),
    3: ("Medium", "Mittel"),
    4: ("Hard", "Schwer"),
    5: ("Very hard", "Sehr schwer"),
}


def _ensure_fonts() -> None:
    missing = [str(p) for p in (FONT_REGULAR, FONT_BOLD) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            "Missing font files: " + ", ".join(missing)
            + ". Put DejaVuSans.ttf and DejaVuSans-Bold.ttf in src/fonts/."
        )


class _BookPDF(FPDF):
    def header(self) -> None:
        if self.page_no() == 1:
            return
        self.set_font("DejaVu", "", 8)
        self.set_text_color(150, 160, 175)
        half = self.epw / 2
        self.cell(half, 6, "BüroKnakker", align="L")
        self.cell(half, 6, f"page {self.page_no()} / {{nb}}", align="R",
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        y = self.get_y()
        self.set_draw_color(220, 226, 233)
        self.set_line_width(0.2)
        self.line(self.l_margin, y, self.w - self.r_margin, y)
        self.ln(4)

    def footer(self) -> None:
        if self.page_no() == 1:
            return
        self.set_y(-14)
        self.set_font("DejaVu", "", 8)
        self.set_text_color(150, 160, 175)
        self.cell(0, 5, "bueroknakker.streamlit.app", align="C")


def _subhead(pdf: FPDF, text: str, colour: tuple[int, int, int]) -> None:
    pdf.set_font("DejaVu", "B", 9)
    pdf.set_text_color(*colour)
    pdf.cell(pdf.epw, 6, text.upper(), **NR)
    y = pdf.get_y()
    pdf.set_draw_color(*colour)
    pdf.set_line_width(0.35)
    pdf.line(pdf.l_margin, y, pdf.l_margin + 18, y)
    pdf.ln(2)


def _body(pdf: FPDF, text: str, size: int = 10,
          colour: tuple[int, int, int] = (30, 40, 55)) -> None:
    pdf.set_font("DejaVu", "", size)
    pdf.set_text_color(*colour)
    pdf.multi_cell(pdf.epw, 5.5, text, **NR)


def _cover_page(pdf: FPDF, profile: UserProfile, resolved: list[ResolvedStep],
                plan: Optional[ActionPlan], lang: str) -> None:
    pdf.add_page()

    pdf.set_fill_color(31, 78, 121)
    pdf.rect(0, 0, pdf.w, 78, style="F")

    pdf.set_xy(0, 24)
    pdf.set_font("DejaVu", "B", 42)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(pdf.w, 18, "BüroKnakker", align="C", **NR)

    pdf.set_font("DejaVu", "", 13)
    subtitle = ("Deutsche Bürokratie, geknackt." if lang == "de"
                else "Germany bureaucracy, cracked.")
    pdf.cell(pdf.w, 8, subtitle, align="C", **NR)

    pdf.set_y(95)
    pdf.set_x(pdf.l_margin)

    pdf.set_font("DejaVu", "B", 14)
    pdf.set_text_color(31, 78, 121)
    pdf.cell(pdf.epw, 10, "Your profile" if lang == "en" else "Dein Profil", **NR)

    rows = [
        ("City" if lang == "en" else "Stadt", profile.city),
        ("Status", profile.status),
        ("Arrival" if lang == "en" else "Ankunft",
         profile.arrival_date.strftime("%d.%m.%Y")),
        ("Reason" if lang == "en" else "Grund",
         {"work": ("Work" if lang == "en" else "Arbeit"),
          "study": ("Study" if lang == "en" else "Studium"),
          "family": ("Family" if lang == "en" else "Familie"),
          "other": ("Other" if lang == "en" else "Sonstiges")}.get(
              profile.move_reason, profile.move_reason)),
        ("Contract" if lang == "en" else "Vertrag",
         {"employee": ("Employee" if lang == "en" else "Angestellt"),
          "student": ("Student" if lang == "en" else "Studium"),
          "freelancer": ("Freelancer" if lang == "en" else "Selbstständig"),
          "unemployed": ("Unemployed" if lang == "en" else "Arbeitssuchend")}.get(
              profile.contract_type, profile.contract_type)),
        ("Family" if lang == "en" else "Familie",
         ("yes" if lang == "en" else "ja") if profile.family
         else ("no" if lang == "en" else "nein")),
    ]
    for label, value in rows:
        pdf.set_font("DejaVu", "B", 11)
        pdf.set_text_color(60, 70, 85)
        pdf.cell(45, 7, f"{label}:", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("DejaVu", "", 11)
        pdf.set_text_color(30, 40, 55)
        pdf.cell(0, 7, str(value), **NR)

    pdf.ln(10)

    total = len(resolved)
    cost_lo = plan.total_cost_min if plan else sum((r.step.cost_eur_min or 0) for r in resolved)
    cost_hi = plan.total_cost_max if plan else sum((r.step.cost_eur_max or 0) for r in resolved)
    duration = plan.total_duration_days if plan else 0

    metrics = [
        ("Steps" if lang == "en" else "Schritte", str(total)),
        ("Cost" if lang == "en" else "Kosten", f"{int(cost_lo)}-{int(cost_hi)} EUR"),
        ("Duration" if lang == "en" else "Dauer",
         f"{duration} days" if lang == "en" else f"{duration} Tage"),
    ]

    col_w = (pdf.epw - 8) / 3
    y0 = pdf.get_y()
    x_start = pdf.l_margin
    for i, (label, value) in enumerate(metrics):
        x = x_start + i * (col_w + 4)
        pdf.set_fill_color(246, 249, 252)
        pdf.set_draw_color(220, 226, 233)
        pdf.set_line_width(0.2)
        pdf.rect(x, y0, col_w, 24, style="DF")
        pdf.set_xy(x + 4, y0 + 4)
        pdf.set_font("DejaVu", "", 8)
        pdf.set_text_color(110, 120, 135)
        pdf.cell(col_w - 8, 5, label.upper(), **NR)
        pdf.set_xy(x + 4, y0 + 10)
        pdf.set_font("DejaVu", "B", 14)
        pdf.set_text_color(31, 78, 121)
        pdf.cell(col_w - 8, 10, value)

    pdf.set_y(y0 + 34)

    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(150, 160, 175)
    gen = datetime.now().strftime("%d.%m.%Y %H:%M")
    pdf.cell(pdf.epw, 5,
             f"Generated on {gen}" if lang == "en" else f"Erstellt am {gen}",
             align="C", **NR)


def _toc_page(pdf: FPDF, resolved: list[ResolvedStep], lang: str) -> None:
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 22)
    pdf.set_text_color(31, 78, 121)
    pdf.cell(pdf.epw, 14, "Contents" if lang == "en" else "Inhalt", **NR)
    pdf.ln(4)

    groups: dict[str, list[ResolvedStep]] = {}
    for r in resolved:
        groups.setdefault(r.step.category.value, []).append(r)

    for cat, items in groups.items():
        label = CATEGORY_LABELS.get(cat, ("Other", "Sonstiges"))
        title = label[0] if lang == "en" else label[1]
        colour = CATEGORY_COLORS_HEX.get(cat, (100, 116, 139))

        pdf.set_font("DejaVu", "B", 12)
        pdf.set_text_color(*colour)
        pdf.cell(0, 8, f"{title}  -  {len(items)}", **NR)

        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(60, 70, 85)
        for r in items:
            name = r.step.title_en if lang == "en" else r.step.title_de
            pdf.cell(0, 6, f"      -  {name}", **NR)
        pdf.ln(2)


def _critical_path_page(pdf: FPDF, plan: ActionPlan, lang: str) -> None:
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 22)
    pdf.set_text_color(31, 78, 121)
    title = "Critical path" if lang == "en" else "Kritischer Pfad"
    pdf.cell(pdf.epw, 14, title, **NR)

    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(110, 120, 135)
    hint = ("The longest dependency chain, step by step." if lang == "en"
            else "Die laengste Abhaengigkeitskette, Schritt fuer Schritt.")
    pdf.cell(pdf.epw, 6, hint, **NR)
    pdf.ln(4)

    label = "Total duration" if lang == "en" else "Gesamtdauer"
    unit = "days" if lang == "en" else "Tage"
    pdf.set_font("DejaVu", "B", 12)
    pdf.set_text_color(31, 78, 121)
    pdf.cell(pdf.epw, 8, f"{label}: {plan.total_duration_days} {unit}", **NR)
    pdf.ln(4)

    cursor = plan.profile.arrival_date
    for i, sid in enumerate(plan.critical_path, start=1):
        r = plan.by_id.get(sid)
        if r is None:
            continue
        s = r.step
        days = s.duration_days or 1
        end = cursor + timedelta(days=days)

        pdf.set_font("DejaVu", "B", 11)
        pdf.set_text_color(30, 40, 55)
        name = s.title_en if lang == "en" else s.title_de
        pdf.cell(0, 6, f"{i}. {name}", **NR)

        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(110, 120, 135)
        pdf.cell(0, 5,
                 f"      {cursor.strftime('%d.%m')}  ->  {end.strftime('%d.%m.%Y')}   -   {days} d",
                 **NR)
        cursor = end
        pdf.ln(2)


def _step_block(pdf: FPDF, r: ResolvedStep, number: int,
                profile: UserProfile, lang: str,
                colour: tuple[int, int, int]) -> None:
    s = r.step

    if pdf.get_y() > pdf.h - 70:
        pdf.add_page()

    W = pdf.epw

    pdf.set_font("DejaVu", "B", 13)
    pdf.set_text_color(30, 40, 55)
    title = s.title_en if lang == "en" else s.title_de
    subtitle = s.title_de if lang == "en" else s.title_en
    pdf.multi_cell(W, 7, f"{number}. {title}", **NR)

    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(110, 120, 135)
    pdf.multi_cell(W, 5, subtitle, **NR)
    pdf.ln(1)

    parts: list[tuple[str, str]] = []
    if r.deadline:
        parts.append(("Deadline" if lang == "en" else "Frist",
                      r.deadline.strftime("%d.%m.%Y")))
    if s.duration_days:
        parts.append(("Duration" if lang == "en" else "Dauer",
                      f"{s.duration_days} d"))
    if s.cost_eur_max:
        parts.append(("Cost" if lang == "en" else "Kosten",
                      f"{int(s.cost_eur_min or 0)}-{int(s.cost_eur_max)} EUR"))
    dlabel = DIFFICULTY_LABELS.get(s.difficulty.value, DIFFICULTY_LABELS[3])
    parts.append(("Difficulty" if lang == "en" else "Schwierigkeit",
                  dlabel[0] if lang == "en" else dlabel[1]))
    if r.blocked_by:
        parts.append(("Blocked by" if lang == "en" else "Blockiert durch",
                      ", ".join(r.blocked_by)))

    for label, value in parts:
        pdf.set_font("DejaVu", "B", 9)
        pdf.set_text_color(90, 100, 115)
        pdf.cell(38, 5, f"{label}:", new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(30, 40, 55)
        pdf.cell(0, 5, str(value), **NR)
    pdf.ln(2)

    notes = s.notes_en if lang == "en" else s.notes_de
    if notes:
        _body(pdf, notes)
        pdf.ln(2)

    if s.documents:
        _subhead(pdf, "Documents" if lang == "en" else "Dokumente", colour)
        for d in s.documents:
            x = pdf.l_margin
            y = pdf.get_y()
            pdf.set_draw_color(150, 160, 175)
            pdf.set_line_width(0.25)
            pdf.rect(x, y + 1.8, 3.5, 3.5)
            pdf.set_xy(x + 7, y)
            pdf.set_font("DejaVu", "", 10)
            pdf.set_text_color(30, 40, 55)
            pdf.multi_cell(W - 7, 6, d, **NR)
        pdf.ln(2)

    tips = s.tips_en if lang == "en" else s.tips_de
    if tips:
        _subhead(pdf, "Tips" if lang == "en" else "Tipps", colour)
        for tip in tips:
            pdf.set_x(pdf.l_margin)
            pdf.set_font("DejaVu", "", 10)
            pdf.set_text_color(30, 40, 55)
            pdf.multi_cell(W, 5.5, f"*  {tip}", **NR)
        pdf.ln(2)

    if s.phrases:
        _subhead(pdf, "Phrases" if lang == "en" else "Saetze", colour)
        for p in s.phrases:
            pdf.set_font("DejaVu", "", 8)
            pdf.set_text_color(110, 120, 135)
            pdf.multi_cell(W, 5, f"[{p.context_de}]", **NR)
            pdf.set_font("DejaVu", "B", 11)
            pdf.set_text_color(31, 78, 121)
            pdf.multi_cell(W, 6, f">>  {p.phrase_de}", **NR)
            pdf.set_font("DejaVu", "", 9)
            pdf.set_text_color(110, 120, 135)
            pdf.multi_cell(W, 5, p.phrase_en, **NR)
            pdf.ln(1)
        pdf.ln(1)

    url = s.link_by_city.get(profile.city) or s.link
    if url:
        pdf.set_font("DejaVu", "", 9)
        pdf.set_text_color(31, 78, 121)
        pdf.multi_cell(W, 5, url, link=url, **NR)
        pdf.ln(2)

    _subhead(pdf, "Notes" if lang == "en" else "Notizen", colour)
    pdf.set_draw_color(220, 226, 233)
    pdf.set_line_width(0.2)
    for _ in range(3):
        y = pdf.get_y() + 4
        pdf.line(pdf.l_margin, y, pdf.w - pdf.r_margin, y)
        pdf.ln(8)

    pdf.ln(4)


def steps_to_pdf(
    resolved: Iterable[ResolvedStep],
    profile: UserProfile,
    lang: str = "en",
    plan: Optional[ActionPlan] = None,
) -> bytes:
    _ensure_fonts()
    resolved = list(resolved)

    pdf = _BookPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.set_margins(left=18, top=18, right=18)
    pdf.alias_nb_pages()

    pdf.add_font("DejaVu", "", str(FONT_REGULAR))
    pdf.add_font("DejaVu", "B", str(FONT_BOLD))

    _cover_page(pdf, profile, resolved, plan, lang)
    _toc_page(pdf, resolved, lang)

    if plan and plan.critical_path:
        _critical_path_page(pdf, plan, lang)

    groups: dict[str, list[ResolvedStep]] = {}
    for r in resolved:
        groups.setdefault(r.step.category.value, []).append(r)

    step_number = 0
    for cat, items in groups.items():
        colour = CATEGORY_COLORS_HEX.get(cat, (100, 116, 139))
        label = CATEGORY_LABELS.get(cat, ("Other", "Sonstiges"))
        title = label[0] if lang == "en" else label[1]

        pdf.add_page()
        pdf.set_fill_color(*colour)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("DejaVu", "B", 18)
        pdf.set_x(pdf.l_margin)
        pdf.cell(pdf.epw, 14, f"   {title}", fill=True, **NR)
        pdf.ln(4)

        for r in items:
            step_number += 1
            _step_block(pdf, r, step_number, profile, lang, colour)

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
