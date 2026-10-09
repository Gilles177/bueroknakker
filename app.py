from datetime import date
from pathlib import Path

import streamlit as st
import yaml

from src.engine import resolve_link, resolve_steps
from src.export import steps_to_ics, steps_to_pdf
from src.i18n import t
from src.models import Step, UserProfile

st.set_page_config(
    page_title="BüroKnakker",
    page_icon="🇩🇪",
    layout="wide",
)

DATA_DIR = Path(__file__).parent / "data"

UMLAUT_MAP = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "ae", "Ö": "oe", "Ü": "ue",
})


def slug(city: str) -> str:
    return city.lower().translate(UMLAUT_MAP)

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


@st.cache_data
def load_steps() -> list[Step]:
    with open(DATA_DIR / "steps.yaml", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return [Step(**s) for s in raw]


@st.cache_data
def load_city(name: str) -> dict:
    path = DATA_DIR / "cities" / f"{slug(name)}.yaml"
    if not path.exists():
        return {
            "name": name,
            "buergeramt_url": None,
            "auslaenderbehoerde_url": None,
            "notes": "No city-specific info yet. Contributions welcome.",
        }
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


steps = load_steps()

# ---------- Sidebar ----------
with st.sidebar:
    st.title("BüroKnakker")
    lang = st.radio("Language / Sprache", ["en", "de"], horizontal=True)
    st.divider()
    st.subheader(t("profile_header", lang))
    city = st.selectbox(t("city", lang), CITIES)
    status = st.selectbox(
        t("status", lang),
        ["EU citizen", "Non-EU student", "Non-EU employee", "Freelancer"],
    )
    arrival = st.date_input(t("arrival", lang), date.today())
    family = st.checkbox(t("family", lang), value=False)

profile = UserProfile(
    city=city,
    status=status,
    arrival_date=arrival,
    family=family,
    language=lang,
)

resolved = resolve_steps(steps, profile)
city_info = load_city(city)

# ---------- Header ----------
st.title("BüroKnakker")
st.caption(t("tagline", lang))
st.write(f"**{len(resolved)}** {t('steps_count', lang)}")

tab_timeline, tab_checklist, tab_city, tab_export = st.tabs(
    [
        t("tab_timeline", lang),
        t("tab_checklist", lang),
        t("tab_city", lang),
        t("tab_export", lang),
    ]
)

# ---------- Timeline ----------
with tab_timeline:
    st.subheader(t("your_timeline", lang))
    if not resolved:
        st.info(t("no_steps", lang))
    for r in resolved:
        s = r.step
        primary = s.title_de if lang == "de" else s.title_en
        secondary = s.title_en if lang == "de" else s.title_de
        with st.expander(f"{primary}  ·  {secondary}"):
            if r.deadline:
                st.write(
                    f"**{t('deadline', lang)}:** "
                    f"{r.deadline.strftime('%d.%m.%Y')}"
                )
                if r.days_left is not None:
                    if r.days_left < 0:
                        st.error(
                            f"{t('overdue', lang)} — "
                            f"{abs(r.days_left)} {t('days', lang)}"
                        )
                    elif r.days_left <= 7:
                        st.warning(
                            f"{r.days_left} {t('days_left', lang)}"
                        )
                    else:
                        st.info(
                            f"{r.days_left} {t('days_left', lang)}"
                        )
            notes = s.notes_de if lang == "de" else s.notes_en
            if notes:
                st.write(notes)
            url = resolve_link(s, city)
            if url:
                st.link_button(t("official_link", lang), url)

# ---------- Checklist ----------
with tab_checklist:
    st.subheader(t("checklist", lang))
    for r in resolved:
        s = r.step
        title = s.title_de if lang == "de" else s.title_en
        with st.expander(title):
            if not s.documents:
                st.write(t("no_documents", lang))
            for i, doc in enumerate(s.documents):
                st.checkbox(doc, key=f"chk-{s.id}-{i}")

# ---------- City info ----------
with tab_city:
    st.subheader(city_info.get("name", city))
    st.write(city_info.get("notes", ""))
    if city_info.get("buergeramt_url"):
        st.markdown(
            f"- [{t('buergeramt', lang)}]({city_info['buergeramt_url']})"
        )
    if city_info.get("auslaenderbehoerde_url"):
        st.markdown(
            f"- [{t('auslaenderbehoerde', lang)}]"
            f"({city_info['auslaenderbehoerde_url']})"
        )

# ---------- Export ----------
with tab_export:
    st.subheader(t("export", lang))
    slug = city.lower()

    pdf_bytes = steps_to_pdf(resolved, profile, lang)
    st.download_button(
        t("download_pdf", lang),
        data=pdf_bytes,
        file_name=f"bueroknakker-{slug}.pdf",
        mime="application/pdf",
    )

    ics_text = steps_to_ics(resolved, profile)
    st.download_button(
        t("download_ics", lang),
        data=ics_text.encode("utf-8"),
        file_name=f"bueroknakker-{slug}.ics",
        mime="text/calendar",
    )
