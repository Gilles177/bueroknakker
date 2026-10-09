from __future__ import annotations

from string import Template

import streamlit as st

CATEGORY_COLORS = {
    "registration": "#3b82f6",
    "tax":          "#8b5cf6",
    "health":       "#10b981",
    "finance":      "#f59e0b",
    "immigration":  "#ef4444",
    "work":         "#06b6d4",
    "family":       "#ec4899",
    "housing":      "#84cc16",
    "transport":    "#6366f1",
    "other":        "#64748b",
}

CATEGORY_ICONS = {
    "registration": "📇",
    "tax":          "🧾",
    "health":       "🏥",
    "finance":      "💶",
    "immigration":  "🛂",
    "work":         "💼",
    "family":       "👨‍👩‍👧",
    "housing":      "🏠",
    "transport":    "🚆",
    "other":        "📌",
}

DIFFICULTY_LABELS = {
    1: ("Trivial", "Trivial"),
    2: ("Easy", "Einfach"),
    3: ("Medium", "Mittel"),
    4: ("Hard", "Schwer"),
    5: ("Very hard", "Sehr schwer"),
}

CHANNEL_ICONS = {
    "online":    "💻",
    "in_person": "🏢",
    "mail":      "✉️",
    "phone":     "📞",
    "mixed":     "🔀",
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


def _palette(dark: bool) -> dict[str, str]:
    if dark:
        return {
            "bg":         "#0e1621",
            "bg_alt":     "#131f2c",
            "card":       "#1a2735",
            "text":       "#e6edf5",
            "muted":      "#8b9aab",
            "border":     "#253340",
            "hero_from":  "#1a3a5c",
            "hero_to":    "#2d6ca3",
            "shadow":     "rgba(0,0,0,0.35)",
        }
    return {
        "bg":         "#ffffff",
        "bg_alt":     "#f6f9fc",
        "card":       "#ffffff",
        "text":       "#1a2b3c",
        "muted":      "#6b7c93",
        "border":     "#e8edf2",
        "hero_from":  "#1f4e79",
        "hero_to":    "#3b82f6",
        "shadow":     "rgba(20,40,60,0.08)",
    }


_CSS = Template("""
<style>
html, body, [class*="css"] {
    font-family: -apple-system, "Inter", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
[data-testid="stAppViewContainer"] { background: $bg; color: $text; }
[data-testid="stSidebar"] { background: $bg_alt; }
.block-container { padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1300px; }

.bk-hero {
    background: linear-gradient(135deg, $hero_from 0%, $hero_to 100%);
    color: white;
    padding: 1.75rem 2rem;
    border-radius: 18px;
    margin-bottom: 1.25rem;
    box-shadow: 0 12px 32px $shadow;
    position: relative;
    overflow: hidden;
}
.bk-hero::after {
    content: "";
    position: absolute;
    right: -60px; top: -60px;
    width: 240px; height: 240px;
    background: radial-gradient(circle, rgba(255,255,255,0.12), transparent 70%);
    border-radius: 50%;
}
.bk-hero h1 { margin: 0 0 0.25rem; font-size: 2.1rem; font-weight: 800; letter-spacing: -0.025em; }
.bk-hero p  { margin: 0; opacity: 0.92; font-size: 1rem; max-width: 720px; }

.bk-kpi-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 1rem; }
.bk-kpi {
    flex: 1 1 180px;
    background: $card;
    color: $text;
    border-radius: 14px;
    padding: 1rem 1.15rem;
    border: 1px solid $border;
    box-shadow: 0 2px 10px $shadow;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    min-width: 160px;
}
.bk-kpi:hover { transform: translateY(-2px); box-shadow: 0 8px 20px $shadow; }
.bk-kpi-label {
    font-size: 0.72rem; font-weight: 700; color: $muted;
    text-transform: uppercase; letter-spacing: 0.06em; margin: 0 0 0.35rem;
}
.bk-kpi-value {
    font-size: 1.65rem; font-weight: 800; color: $text;
    line-height: 1.1; margin: 0; letter-spacing: -0.02em;
}
.bk-kpi-sub { font-size: 0.78rem; color: $muted; margin: 0.2rem 0 0; }

.bk-card {
    background: $card; color: $text;
    border-radius: 12px;
    padding: 1rem 1.15rem;
    border: 1px solid $border;
    margin-bottom: 0.6rem;
    box-shadow: 0 1px 4px $shadow;
}
.bk-card-title { font-weight: 700; font-size: 0.98rem; color: $text; margin: 0 0 0.2rem; }
.bk-card-meta  { font-size: 0.78rem; color: $muted; margin: 0 0 0.35rem; }

.bk-pill {
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    font-size: 0.71rem; font-weight: 700; margin-right: 5px; margin-bottom: 3px;
    color: white; letter-spacing: 0.01em;
}
.bk-pill-soft {
    display: inline-block; padding: 2px 10px; border-radius: 999px;
    font-size: 0.71rem; font-weight: 600; margin-right: 5px; margin-bottom: 3px;
    background: $bg_alt; color: $muted;
}

.bk-col-head {
    font-weight: 800; font-size: 0.85rem; text-transform: uppercase;
    letter-spacing: 0.08em; color: $muted;
    margin-bottom: 0.6rem; padding-bottom: 0.4rem; border-bottom: 2px solid $border;
}
.bk-kcard {
    background: $card; color: $text;
    border-left: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 0.7rem 0.85rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 3px $shadow;
    font-size: 0.85rem;
}
.bk-kcard-title { font-weight: 700; color: $text; margin-bottom: 0.15rem; }
.bk-kcard-meta  { color: $muted; font-size: 0.75rem; }

.bk-section {
    font-weight: 800; font-size: 1.05rem; color: $text;
    margin: 1rem 0 0.5rem; letter-spacing: -0.01em;
}
.bk-section-sub { font-size: 0.82rem; color: $muted; margin: -0.25rem 0 0.75rem; }

.bk-detail-meta {
    background: $bg_alt; color: $muted;
    border-radius: 10px; padding: 0.75rem 1rem;
    margin: 0.5rem 0 0.75rem; font-size: 0.85rem; line-height: 1.7;
}
.bk-detail-meta b { color: $text; }

.bk-phrase {
    background: $bg_alt;
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    margin-bottom: 0.6rem;
    border: 1px solid $border;
}
.bk-phrase-ctx {
    font-size: 0.72rem; font-weight: 700; color: $muted;
    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.35rem;
}
.bk-phrase-de { font-size: 1.02rem; font-weight: 700; color: $hero_from; margin-bottom: 0.15rem; }
.bk-phrase-en { font-size: 0.85rem; color: $muted; font-style: italic; }
</style>
""")


def inject_css(dark: bool = False) -> None:
    st.markdown(_CSS.substitute(**_palette(dark)), unsafe_allow_html=True)


def category_color(cat: str) -> str:
    return CATEGORY_COLORS.get(cat, CATEGORY_COLORS["other"])


def category_icon(cat: str) -> str:
    return CATEGORY_ICONS.get(cat, CATEGORY_ICONS["other"])


def category_label(cat: str, lang: str) -> str:
    pair = CATEGORY_LABELS.get(cat, CATEGORY_LABELS["other"])
    return pair[0] if lang == "en" else pair[1]


def difficulty_label(level: int, lang: str) -> str:
    pair = DIFFICULTY_LABELS.get(level, DIFFICULTY_LABELS[3])
    return pair[0] if lang == "en" else pair[1]


def channel_icon(channel: str) -> str:
    return CHANNEL_ICONS.get(channel, "")
