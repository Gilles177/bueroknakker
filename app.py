from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yaml

from src.engine import build_plan, resolve_link
from src.export import steps_to_ics, steps_to_pdf
from src.i18n import t
from src.models import FamilyMember, Step, UserProfile
from src.theme import (
    category_color,
    category_icon,
    category_label,
    channel_icon,
    difficulty_label,
    inject_css,
)
from src.utils import (
    days_label,
    format_date,
    format_eur,
    slug,
    urgency_color,
    urgency_label,
)

# ----------------------------------------------------------------- setup

st.set_page_config(page_title="BüroKnakker", page_icon="🇩🇪", layout="wide")
inject_css()

DATA_DIR = Path(__file__).parent / "data"

CITIES = [
    "Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt", "Stuttgart",
    "Düsseldorf", "Leipzig", "Dresden", "Nuremberg", "Hannover", "Bremen",
]

STATUSES = ["EU citizen", "Non-EU student", "Non-EU employee", "Freelancer"]
MOVE_REASONS = ["work", "study", "family", "other"]
CONTRACT_TYPES = ["employee", "student", "freelancer", "unemployed"]


@st.cache_data
def load_steps() -> list[Step]:
    raw = yaml.safe_load((DATA_DIR / "steps.yaml").read_text(encoding="utf-8"))
    return [Step(**s) for s in raw]


@st.cache_data
def load_city(name: str) -> dict:
    path = DATA_DIR / "cities" / f"{slug(name)}.yaml"
    if not path.exists():
        return {"name": name, "notes": "No city info yet."}
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ----------------------------------------------------------------- state

if "done" not in st.session_state:
    st.session_state.done = {}
if "notes" not in st.session_state:
    st.session_state.notes = {}


# ----------------------------------------------------------------- sidebar

with st.sidebar:
    st.markdown("### 🇩🇪 BüroKnakker")
    lang = st.radio("Language / Sprache", ["en", "de"], horizontal=True, label_visibility="collapsed")
    st.divider()

    st.markdown(f"**{t('profile_header', lang)}**")
    city = st.selectbox(t("city", lang), CITIES, index=0)
    status = st.selectbox(t("status", lang), STATUSES, index=0)
    arrival = st.date_input(t("arrival", lang), date.today())
    move_reason = st.selectbox(t("move_reason", lang), MOVE_REASONS, index=0)
    contract_type = st.selectbox(t("contract_type", lang), CONTRACT_TYPES, index=0)
    family = st.checkbox(t("family", lang), value=False)

    members: list[FamilyMember] = []
    if family:
        n = st.number_input(t("members", lang), min_value=1, max_value=6, value=1, step=1)
        for i in range(int(n)):
            st.markdown(f"*{t('member_name', lang)} {i + 1}*")
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                mname = st.text_input("Name", key=f"m_name_{i}", label_visibility="collapsed")
            with c2:
                rel = st.selectbox(
                    t("member_relation", lang),
                    ["spouse", "child", "other"],
                    key=f"m_rel_{i}",
                    label_visibility="collapsed",
                )
            with c3:
                age = st.number_input(
                    t("member_age", lang),
                    min_value=0, max_value=120, value=30, step=1,
                    key=f"m_age_{i}",
                    label_visibility="collapsed",
                )
            members.append(FamilyMember(name=mname or f"Member {i+1}", relation=rel, age=int(age)))

    st.divider()
    done_count = sum(1 for v in st.session_state.done.values() if v)
    if st.button(t("reset_state", lang), use_container_width=True):
        st.session_state.done = {}
        st.session_state.notes = {}
        st.rerun()


profile = UserProfile(
    city=city,
    status=status,
    arrival_date=arrival,
    move_reason=move_reason,
    contract_type=contract_type,
    family=family,
    members=members,
    language=lang,
)

steps = load_steps()
plan = build_plan(steps, profile)
city_info = load_city(city)

# ----------------------------------------------------------------- helpers


def is_done(sid: str) -> bool:
    return st.session_state.done.get(sid, False)


def step_card(r, show_category: bool = True) -> None:
    s = r.step
    cat = s.category.value
    color = category_color(cat)
    icon = category_icon(cat)
    title = s.title_de if lang == "de" else s.title_en
    sub = s.title_en if lang == "de" else s.title_de

    overdue = r.days_left is not None and r.days_left < 0
    done = is_done(s.id)
    strike = "text-decoration: line-through; opacity: 0.55;" if done else ""

    pills = []
    if r.deadline:
        pills.append(
            f'<span class="bk-pill" style="background:{urgency_color(r.days_left)}">'
            f'{urgency_label(r.days_left, lang)}</span>'
        )
    if show_category:
        pills.append(
            f'<span class="bk-pill-soft">{icon} {category_label(cat, lang)}</span>'
        )
    if s.difficulty.value >= 4:
        pills.append(f'<span class="bk-pill-soft">⚡ {difficulty_label(s.difficulty.value, lang)}</span>')
    if s.cost_eur_max:
        pills.append(f'<span class="bk-pill-soft">💶 {format_eur(s.cost_eur_max)}</span>')

    meta = f"{icon} {sub}"
    if r.deadline:
        meta += f" · {t('deadline', lang)}: {format_date(r.deadline)}"
    if r.days_left is not None:
        meta += f" · {days_label(r.days_left, lang)}"

    st.markdown(
        f"""
        <div class="bk-card" style="border-left: 4px solid {color}; {strike}">
            <div class="bk-card-title">{title}</div>
            <div class="bk-card-meta">{meta}</div>
            <div>{''.join(pills)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------- hero

st.markdown(
    f"""
    <div class="bk-hero">
        <h1>BüroKnakker</h1>
        <p>{t('tagline', lang)} {t('subtitle', lang)}</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------- tabs

tabs = st.tabs([
    t("tab_dashboard", lang),
    t("tab_timeline", lang),
    t("tab_kanban", lang),
    t("tab_calendar", lang),
    t("tab_cost", lang),
    t("tab_search", lang),
    t("tab_phrasebook", lang),
    t("tab_export", lang),
])


# ================================================================ dashboard
with tabs[0]:
    n_steps = plan.total_steps
    n_ready = len(plan.ready_now)
    n_overdue = sum(1 for r in plan.steps if r.days_left is not None and r.days_left < 0)
    cost_lo = format_eur(plan.total_cost_min)
    cost_hi = format_eur(plan.total_cost_max)
    dur = plan.total_duration_days
    dur_unit = t("kpi_days", lang)

    next_deadline = next(
        (r for r in plan.steps if r.deadline and r.days_left is not None and r.days_left >= 0),
        None,
    )
    nd_val = format_date(next_deadline.deadline) if next_deadline else "—"
    nd_sub = days_label(next_deadline.days_left, lang) if next_deadline else ""

    st.markdown(
        f"""
        <div class="bk-kpi-row">
            <div class="bk-kpi">
                <div class="bk-kpi-label">{t('kpi_steps', lang)}</div>
                <div class="bk-kpi-value">{n_steps}</div>
                <div class="bk-kpi-sub">{done_count} {t('steps_done', lang)}</div>
            </div>
            <div class="bk-kpi">
                <div class="bk-kpi-label">{t('kpi_cost', lang)}</div>
                <div class="bk-kpi-value">{cost_lo} – {cost_hi}</div>
                <div class="bk-kpi-sub">min – max</div>
            </div>
            <div class="bk-kpi">
                <div class="bk-kpi-label">{t('kpi_duration', lang)}</div>
                <div class="bk-kpi-value">{dur} {dur_unit}</div>
                <div class="bk-kpi-sub">from {format_date(profile.arrival_date)}</div>
            </div>
            <div class="bk-kpi">
                <div class="bk-kpi-label">{t('kpi_ready', lang)}</div>
                <div class="bk-kpi-value">{n_ready}</div>
                <div class="bk-kpi-sub">{len(plan.blocked)} {t('blocked', lang).lower()}</div>
            </div>
            <div class="bk-kpi">
                <div class="bk-kpi-label">{t('kpi_overdue', lang)}</div>
                <div class="bk-kpi-value" style="color:{'#dc2626' if n_overdue else '#10b981'}">{n_overdue}</div>
                <div class="bk-kpi-sub">&nbsp;</div>
            </div>
            <div class="bk-kpi">
                <div class="bk-kpi-label">{t('kpi_next_deadline', lang)}</div>
                <div class="bk-kpi-value" style="font-size:1.15rem">{nd_val}</div>
                <div class="bk-kpi-sub">{nd_sub}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns([3, 2])

    with col_a:
        st.markdown(f'<div class="bk-section">⚡ {t("next_actions", lang)}</div>', unsafe_allow_html=True)
        ready_steps = [r for r in plan.steps if r.step.id in plan.ready_now and not is_done(r.step.id)]
        ready_steps.sort(key=lambda r: (r.deadline is None, r.deadline or date.max))
        if not ready_steps:
            st.success(t("no_next_actions", lang))
        for r in ready_steps[:5]:
            step_card(r)

    with col_b:
        st.markdown(f'<div class="bk-section">🔒 {t("blockers_title", lang)}</div>', unsafe_allow_html=True)
        blocked = [r for r in plan.steps if r.blocked_by]
        if not blocked:
            st.info(t("blockers_none", lang))
        for r in blocked[:5]:
            s = r.step
            blocked_names = ", ".join(
                (plan.by_id[b].step.title_en if b in plan.by_id else b) for b in r.blocked_by
            )
            st.markdown(
                f"""
                <div class="bk-card">
                    <div class="bk-card-title">{s.title_en if lang == 'en' else s.title_de}</div>
                    <div class="bk-card-meta">{t('blocked_by', lang)}: {blocked_names}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if plan.critical_path:
        st.markdown(f'<div class="bk-section">🛤️ {t("critical_path", lang)}</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="bk-section-sub">{t("critical_path_hint", lang)} · {dur} {dur_unit}</div>',
            unsafe_allow_html=True,
        )
        for i, sid in enumerate(plan.critical_path):
            if sid not in plan.by_id:
                continue
            r = plan.by_id[sid]
            arrow = "→ " if i else ""
            s = r.step
            st.markdown(
                f'<span class="bk-pill-soft">{arrow}{category_icon(s.category.value)} '
                f'{s.title_en if lang == "en" else s.title_de}'
                f'{" · " + str(s.duration_days) + "d" if s.duration_days else ""}</span>',
                unsafe_allow_html=True,
            )


# ================================================================ timeline
with tabs[1]:
    rows = []
    for r in plan.steps:
        if not r.deadline:
            continue
        s = r.step
        dur = s.duration_days or 1
        end = r.deadline
        start = end - timedelta(days=dur)
        if start < profile.arrival_date:
            start = profile.arrival_date
        rows.append({
            "Step": f"{category_icon(s.category.value)} {s.title_en if lang == 'en' else s.title_de}",
            "Start": start,
            "Finish": end,
            "Category": category_label(s.category.value, lang),
            "Color": category_color(s.category.value),
            "Days left": r.days_left,
            "Urgency": urgency_label(r.days_left, lang),
        })

    if rows:
        df = pd.DataFrame(rows)
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Step",
            color="Category",
            hover_data=["Urgency", "Days left"],
            color_discrete_map={
                category_label(c, lang): category_color(c)
                for c in ["registration", "tax", "health", "finance", "immigration",
                          "work", "family", "housing", "transport", "other"]
            },
        )
        fig.update_yaxes(autorange="reversed", title="")
        fig.update_xaxes(title="")
        fig.update_layout(
            height=max(420, 34 * len(rows)),
            margin=dict(l=10, r=10, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="-apple-system, Inter, sans-serif", size=12),
        )
        fig.update_traces(marker=dict(line=dict(width=0)))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(rows)} steps with a deadline · bar length ≈ estimated duration")
    else:
        st.info(t("no_steps", lang))

    st.markdown(f'<div class="bk-section">📋 {t("tab_timeline", lang)}</div>', unsafe_allow_html=True)
    for r in plan.steps:
        with st.expander(
            f"{category_icon(r.step.category.value)} "
            f"{r.step.title_en if lang == 'en' else r.step.title_de}"
        ):
            s = r.step
            cols = st.columns([1, 1, 1, 1])
            cols[0].markdown(f"**{t('deadline', lang)}**  \n{format_date(r.deadline)}")
            cols[1].markdown(f"**{t('duration', lang)}**  \n{s.duration_days or '—'} {t('days', lang)}")
            cols[2].markdown(
                f"**{t('cost', lang)}**  \n"
                f"{format_eur(s.cost_eur_min)} – {format_eur(s.cost_eur_max)}"
            )
            cols[3].markdown(
                f"**{t('difficulty', lang)}**  \n{difficulty_label(s.difficulty.value, lang)}"
            )
            notes = s.notes_en if lang == "en" else s.notes_de
            if notes:
                st.write(notes)
            if s.documents:
                st.markdown(f"**{t('documents', lang)}**")
                for d in s.documents:
                    st.checkbox(d, key=f"doc-{s.id}-{d}", disabled=True)
            tips = s.tips_en if lang == "en" else s.tips_de
            if tips:
                st.markdown(f"**{t('tips', lang)}**")
                for tip in tips:
                    st.markdown(f"- {tip}")
            url = resolve_link(s, profile.city)
            if url:
                st.link_button(t("official_link", lang), url, use_container_width=True)


# ================================================================ kanban
with tabs[2]:
    col_ready, col_blocked, col_done = st.columns(3)

    with col_ready:
        st.markdown(f'<div class="bk-col-head">🟢 {t("ready_now", lang)}</div>', unsafe_allow_html=True)
        ready = [r for r in plan.steps if r.step.id in plan.ready_now and not is_done(r.step.id)]
        ready.sort(key=lambda r: (r.deadline is None, r.deadline or date.max))
        for r in ready:
            s = r.step
            st.markdown(
                f"""
                <div class="bk-kcard" style="border-left-color:{urgency_color(r.days_left)}">
                    <div class="bk-kcard-title">{category_icon(s.category.value)} {s.title_en if lang == 'en' else s.title_de}</div>
                    <div class="bk-kcard-meta">{format_date(r.deadline)} · {days_label(r.days_left, lang) or '—'}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.checkbox(t("mark_done", lang), key=f"done-{s.id}",
                        value=is_done(s.id),
                        on_change=lambda sid=s.id: st.session_state.done.__setitem__(
                            sid, not st.session_state.done.get(sid, False)
                        ))

    with col_blocked:
        st.markdown(f'<div class="bk-col-head">🔒 {t("blocked", lang)}</div>', unsafe_allow_html=True)
        blocked = [r for r in plan.steps if r.blocked_by and not is_done(r.step.id)]
        for r in blocked:
            s = r.step
            deps = ", ".join(
                (plan.by_id[b].step.title_en if b in plan.by_id else b) for b in r.blocked_by
            )
            st.markdown(
                f"""
                <div class="bk-kcard" style="border-left-color:#64748b">
                    <div class="bk-kcard-title">{category_icon(s.category.value)} {s.title_en if lang == 'en' else s.title_de}</div>
                    <div class="bk-kcard-meta">⛔ {deps}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_done:
        st.markdown(f'<div class="bk-col-head">✅ {t("completed", lang)}</div>', unsafe_allow_html=True)
        done = [r for r in plan.steps if is_done(r.step.id)]
        if not done:
            st.caption(t("no_completed", lang))
        for r in done:
            s = r.step
            st.markdown(
                f"""
                <div class="bk-kcard" style="border-left-color:#10b981; opacity:0.7">
                    <div class="bk-kcard-title">✅ {s.title_en if lang == 'en' else s.title_de}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ================================================================ calendar
with tabs[3]:
    cal_rows = []
    for r in plan.steps:
        if r.deadline:
            cal_rows.append({"date": r.deadline, "step": r.step})
    if cal_rows:
        df = pd.DataFrame([
            {"date": row["date"], "count": 1, "step": row["step"].title_en}
            for row in cal_rows
        ])
        df["date"] = pd.to_datetime(df["date"])
        grouped = df.groupby("date").size().reset_index(name="count")
        grouped["date"] = pd.to_datetime(grouped["date"])
        grouped["month"] = grouped["date"].dt.strftime("%Y-%m")
        grouped["day"] = grouped["date"].dt.day

        months = sorted(grouped["month"].unique())
        cols = st.columns(min(3, len(months)))
        for i, month in enumerate(months):
            sub = grouped[grouped["month"] == month]
            with cols[i % len(cols)]:
                fig = px.bar(
                    sub, x="day", y="count",
                    title=month,
                    color="count",
                    color_continuous_scale=["#dbeafe", "#3b82f6", "#1f4e79"],
                )
                fig.update_layout(
                    height=220, showlegend=False,
                    margin=dict(l=10, r=10, t=40, b=10),
                    coloraxis_showscale=False,
                    plot_bgcolor="white",
                    xaxis=dict(dtick=1, title=""),
                    yaxis=dict(title=""),
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(t("no_steps", lang))


# ================================================================ cost
with tabs[4]:
    cost_rows = []
    for r in plan.steps:
        s = r.step
        if s.cost_eur_max:
            cost_rows.append({
                "step": s.title_en if lang == "en" else s.title_de,
                "min": s.cost_eur_min or 0,
                "max": s.cost_eur_max or 0,
                "category": category_label(s.category.value, lang),
                "date": r.deadline or profile.arrival_date,
            })

    if cost_rows:
        df = pd.DataFrame(cost_rows)
        c1, c2 = st.columns([2, 1])
        with c1:
            fig = px.bar(
                df.sort_values("max", ascending=True),
                x="max", y="step", orientation="h",
                color="category",
                labels={"max": "EUR", "step": ""},
                title=t("chart_cost_per_step", lang),
            )
            fig.update_layout(
                height=max(320, 26 * len(df)),
                margin=dict(l=10, r=10, t=50, b=10),
                plot_bgcolor="white",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig2 = px.pie(
                df, names="category", values="max",
                title=t("chart_categories", lang),
                hole=0.5,
            )
            fig2.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10))
            st.plotly_chart(fig2, use_container_width=True)

        df["date"] = pd.to_datetime(df["date"])
        df_sorted = df.sort_values("date")
        df_sorted["cumulative"] = df_sorted["max"].cumsum()
        fig3 = px.area(
            df_sorted, x="date", y="cumulative",
            title=t("chart_cumulative", lang),
            color_discrete_sequence=["#1f4e79"],
        )
        fig3.update_layout(
            height=280, margin=dict(l=10, r=10, t=50, b=10),
            plot_bgcolor="white",
            xaxis_title="", yaxis_title="EUR",
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No costs associated with your current plan.")


# ================================================================ search
with tabs[5]:
    st.markdown(f'<div class="bk-section">🔎 {t("search", lang)}</div>', unsafe_allow_html=True)
    q = st.text_input(t("search", lang), placeholder=t("search_placeholder", lang), label_visibility="collapsed")
    if q:
        ql = q.lower()
        hits = []
        for r in plan.steps:
            s = r.step
            blob = " ".join([
                s.title_en, s.title_de,
                s.description_en, s.description_de,
                s.notes_en, s.notes_de,
                " ".join(s.documents),
                " ".join(s.tips_en), " ".join(s.tips_de),
            ]).lower()
            if ql in blob:
                hits.append(r)
        st.caption(f"{len(hits)} {t('search_results', lang)}")
        for r in hits:
            step_card(r)
        if not hits:
            st.warning(t("search_no_results", lang))


# ================================================================ phrasebook
with tabs[6]:
    st.markdown(f'<div class="bk-section">💬 {t("phrasebook_title", lang)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="bk-section-sub">{t("copy_hint", lang)}</div>', unsafe_allow_html=True)

    has_phrases = False
    for r in plan.steps:
        s = r.step
        if not s.phrases:
            continue
        has_phrases = True
        st.markdown(
            f'<div class="bk-section">{category_icon(s.category.value)} '
            f'{s.title_en if lang == "en" else s.title_de}</div>',
            unsafe_allow_html=True,
        )
        for p in s.phrases:
            st.markdown(
                f"""
                <div class="bk-phrase">
                    <div class="bk-phrase-ctx">{p.context_de}</div>
                    <div class="bk-phrase-de">{p.phrase_de}</div>
                    <div class="bk-phrase-en">{p.phrase_en}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    if not has_phrases:
        st.info("No phrases for your current plan.")


# ================================================================ export
with tabs[7]:
    st.markdown(f'<div class="bk-section">📤 {t("export_title", lang)}</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1:
        pdf = steps_to_pdf(plan.steps, profile, lang)
        st.download_button(
            t("download_pdf", lang),
            data=pdf,
            file_name=f"bueroknakker-{slug(profile.city)}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with c2:
        ics = steps_to_ics(plan.steps, profile)
        st.download_button(
            t("download_ics", lang),
            data=ics.encode("utf-8"),
            file_name=f"bueroknakker-{slug(profile.city)}.ics",
            mime="text/calendar",
            use_container_width=True,
        )
    with c3:
        snapshot = {
            "profile": profile.model_dump(mode="json"),
            "done": st.session_state.done,
            "notes": st.session_state.notes,
            "plan": [
                {
                    "id": r.step.id,
                    "title_en": r.step.title_en,
                    "title_de": r.step.title_de,
                    "deadline": r.deadline.isoformat() if r.deadline else None,
                    "days_left": r.days_left,
                    "blocked_by": r.blocked_by,
                }
                for r in plan.steps
            ],
            "summary": {
                "total_steps": plan.total_steps,
                "cost_min": plan.total_cost_min,
                "cost_max": plan.total_cost_max,
                "duration_days": plan.total_duration_days,
            },
        }
        st.download_button(
            t("download_json", lang),
            data=json.dumps(snapshot, ensure_ascii=False, indent=2).encode("utf-8"),
            file_name=f"bueroknakker-{slug(profile.city)}.json",
            mime="application/json",
            use_container_width=True,
        )


# ================================================================ city info (footer)
with st.expander(f"ℹ️ {city_info.get('name', city)}"):
    st.write(city_info.get("notes", ""))
    for label, key in [
        ("Bürgeramt", "buergeramt_url"),
        ("Ausländerbehörde", "auslaenderbehoerde_url"),
        ("Finanzamt", "finanzamt_url"),
        ("Kita", "kita_url"),
    ]:
        url = city_info.get(key)
        if url:
            st.markdown(f"- [{label}]({url})")
