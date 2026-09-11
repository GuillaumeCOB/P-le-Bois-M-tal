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


def set_subtask_done(project_id: str, subtask_id: str, state_key: str):
    run_db_action(
        "update_subtask",
        project_id,
        subtask_id,
        {"done": bool(st.session_state.get(state_key, False))},
    )
