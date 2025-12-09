# Code ist in Anlehnung an: https://gist.github.com/treuille/2ce0acb6697f205e44e3e0f576e810b7 geschrieben
import streamlit as st


def display_random_items(items: list[str], cards_per_page=3):
    n_pages = (len(items) - 1) // cards_per_page + 1
    if "page" not in st.session_state:
        st.session_state.page = 0
    page = st.session_state.page
    start = page * cards_per_page
    end = start + cards_per_page
    # Cards für die aktuelle Seite
    selected_cards = items[start:end]
    display_cards = ['<div class="random-grid">']

    for item in selected_cards:
        display_cards.append(item)
    display_cards.append("</div>")
    st.markdown("".join(display_cards), unsafe_allow_html=True)
    col_prev, col_free, col_next = st.columns([1, 16, 1])

    with col_prev:
        st.markdown('<div class="paginator-button">', unsafe_allow_html=True)
        if st.button("⟨", key=f"prev", disabled=(page == 0)):
            st.session_state.page = page - 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_next:
        st.markdown('<div class="paginator-button">', unsafe_allow_html=True)
        if st.button("⟩", key=f"next", disabled=(page == n_pages - 1)):
            st.session_state.page = page + 1
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)