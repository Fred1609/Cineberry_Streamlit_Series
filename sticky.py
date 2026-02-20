import streamlit as st

# CSS einlesen
with open("page_styles.html", "r") as f:
    css = f.read()
st.set_page_config(layout="wide")
st.markdown(css, unsafe_allow_html=True)

# Seiten festlegen
page1 = st.Page("seiten/seite1.py", title="Startseite")
page2 = st.Page("seiten/seite2.py", title="Stöbern")
#page3 = st.Page("seiten/seite3.py", title="Watchlist")

# Navigationsstruktur festlegen
pages_config = {
    "": [page1, page2]
    #"": [page1],
    #"Aufklappmenü": [page2],
}

# Navigationsstruktur erstellen
navigation = st.navigation(pages_config, position="top")
navigation.run()