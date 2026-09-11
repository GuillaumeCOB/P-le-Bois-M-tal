import streamlit as st

import storage as db
from config import DATA_CACHE_TTL_SECONDS, PATH


@st.cache_data(ttl=DATA_CACHE_TTL_SECONDS, show_spinner=False)
def load_data_cached() -> dict:
    return db.load_data(PATH)


def invalidate_data_cache():
    load_data_cached.clear()


def force_refresh():
    invalidate_data_cache()


def toggle_session_flag(key: str):
    st.session_state[key] = not st.session_state.get(key, False)


def run_db_action(action_name: str, *args):
    """Exécute une écriture Supabase puis invalide le cache de lecture."""
    action = getattr(db, action_name)
    action(PATH, *args)
    invalidate_data_cache()


def set_invoice_state_from_widget(
    level: str,
    project_id: str,
    entity_id: str | None,
    state_key: str,
):
    run_db_action(
        "set_invoice_state",
        level,
        project_id,
        entity_id,
        bool(st.session_state.get(state_key, False)),
    )
