"""Session state helpers.

Persistence strategy:
  - `done` flag per step is encoded in the URL query string (?done=a,b,c).
    This survives a page refresh and can be shared as a link.
  - `notes` live only in the session. Use the JSON export in the Export tab
    if you want to keep them long-term.
"""
from __future__ import annotations

import streamlit as st


def load_done_from_query() -> dict[str, bool]:
    raw = st.query_params.get("done", "")
    if not raw:
        return {}
    return {sid: True for sid in raw.split(",") if sid}


def save_done_to_query(done: dict[str, bool]) -> None:
    ids = sorted(sid for sid, v in done.items() if v)
    if ids:
        st.query_params["done"] = ",".join(ids)
    else:
        try:
            del st.query_params["done"]
        except (KeyError, TypeError):
            pass


def toggle_done(sid: str) -> None:
    """Callback used by checkbox on_change handlers."""
    current = st.session_state.done.get(sid, False)
    st.session_state.done[sid] = not current
    save_done_to_query(st.session_state.done)


def reset_done() -> None:
    st.session_state.done = {}
    save_done_to_query({})
