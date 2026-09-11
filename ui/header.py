import streamlit as st

from config import LOGO_PATH
from data_service import force_refresh
from ui.components import ui_container


def render_header():
    with ui_container("top_actionbar", "actionbar"):
        c1, c2, c3 = st.columns([1.15, 4.55, 1.0], vertical_alignment="center")
        with c1:
            if LOGO_PATH.exists():
                st.image(str(LOGO_PATH), use_container_width=True)
        with c2:
            st.markdown(
                """
                <div class="pbm-headline">
                    <div class="pbm-eyebrow">Builders · verticalsea</div>
                    <h1>Suivi de projets - Structures Bois / Métal & Béton</h1>
                    <div class="pbm-subline">Tableau de bord compact, filtrable et aligné sur la charte graphique.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.write("")
            st.button(
                "🔄 Rafraîchir",
                use_container_width=True,
                on_click=force_refresh,
            )
