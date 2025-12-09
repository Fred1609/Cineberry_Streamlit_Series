import streamlit as st

st.set_page_config(layout="wide")

col1, col2, col3 = st.columns(3)
st.session_state["optionen"] = None
st.session_state["slider"] = None
st.session_state["checkbox"] = None
st.session_state["text"] = None

with col1:
    st.title("Spalte 1")
    st.color_picker("Farbe auswählen", "#00f900")
    optionen = st.multiselect(
        "Was magst du?",
        ["Pizza", "Pasta", "Döner", "Sushi",
         "Veggie", "Vegan", "Deutsche Küche"],
        default=["Pizza"],
    )
    st.session_state["optionen"] = optionen

with col2:
    st.title("Spalte 2")
    with st.form("my_form"):
        st.write("Das ist ein Formular")
        slider_val = st.slider("Temperatur", 0.0, 2.0, (0.0, 0.4))
        checkbox_val = st.checkbox("Checkbox")
        text_val = st.text_input(label="Ihre Eingabe", placeholder="Bitte schreiben Sie einen Kommentar!")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state["slider"] = slider_val
            st.session_state["checkbox"] = checkbox_val
            st.session_state["text"] = text_val
    st.write("Das ist außerhalb des Formulars")

with col3:
    st.title("Spalte 3")
    st.write("Lieblingsgericht(e)", st.session_state["optionen"])
    st.divider()
    st.write("Slider-Wert", st.session_state["slider"])
    st.divider()
    st.write("Checkbox-Wert", st.session_state["checkbox"])
    with st.expander("Hier der Kommentar"):
        st.write(st.session_state["text"])

