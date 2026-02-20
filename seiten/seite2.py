import urllib.parse as up
from typing import Any
import streamlit as st
import json
from tantivy import Query, Index, SchemaBuilder, Occur

import utils

# Konstanten
TMDB_PATH = "https://image.tmdb.org/t/p/original"
TMDB_PATH_SMALL = "https://image.tmdb.org/t/p/w200"
INDEX_PATH = "serien_300"  # bestehendes Tantivy-Index-Verzeichnis
TOP_K = 20          # wie viele Ergebnisse angezeigt werden sollen
CARDS_PER_PAGE = 3 # Cards, die in der zufälligen Anzeige auftauchen

schema_builder = SchemaBuilder()
# Text-Felder
schema_builder.add_text_field("wikidata", stored=True)
schema_builder.add_text_field("url", stored=True)
schema_builder.add_text_field("title", stored=True, tokenizer_name='en_stem')
schema_builder.add_text_field("description", stored=True, tokenizer_name='en_stem')  # Multi-valued text field
schema_builder.add_text_field("image", stored=True)
schema_builder.add_text_field("locations", stored=True)
schema_builder.add_text_field("countries", stored=True)
schema_builder.add_text_field("genres", stored=True)
schema_builder.add_text_field("tmdb_overview", stored=True, tokenizer_name='en_stem')
schema_builder.add_text_field("tmdb_poster_path", stored=True)
schema_builder.add_text_field("trailer", stored=True)

# Integer-Felder
schema_builder.add_integer_field("id", stored=True, indexed=True)
schema_builder.add_integer_field("follower", stored=True, fast=True)
schema_builder.add_integer_field("score", stored=True, fast=True)
schema_builder.add_integer_field("start", stored=True, fast=True)
schema_builder.add_integer_field("tmdb_genre_ids", stored=True, indexed=True)
schema_builder.add_integer_field("tmdb_vote_count", stored=True, fast=True)

# Float-Felder
schema_builder.add_float_field("tmdb_popularity", stored=True, fast=True)
schema_builder.add_float_field("tmdb_vote_average", stored=True, fast=True)

# Facettenfelder
schema_builder.add_facet_field("facet_locations")
schema_builder.add_facet_field("facet_countries")
schema_builder.add_facet_field("facet_genres")

schema = schema_builder.build()
index = Index(schema, path=str(INDEX_PATH))
index.reload()
searcher = index.searcher()

st.set_page_config(layout="wide")
with open("styles.html", "r") as f:
    css = f.read()

st.markdown(css, unsafe_allow_html=True)

st.markdown(
    """
    <style>
    [data-testid="stColumn"]:nth-of-type(2){
        border-left: 1.5px solid white;
        padding: 1em 3em 2em 3em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

full_star = '<i class="fa-solid fa-star"></i>'
half_star = '<i class="fa-solid fa-star-half-stroke"></i>'
empty_star = '<i class="fa-regular fa-star"></i>'


# Hilfsfunktion für Seitenrouting mit Anfrageparametern.
# Gibt die Query-Parameter der aktuellen Seite als Dictionary zurück.
# Falls `st.query_params` nicht verfügbar ist, wird ein leeres Dictionary zurückgegeben.
def get_qp() -> dict[str, Any]:
    return getattr(st, "query_params", {})


qp = get_qp()
view = qp.get("view")
selected_id = qp.get("id")
q = qp.get("q", "")  # <-- keep the query in the URL


# ----- Columns definieren -----

col1, col2 = st.columns([4,11], gap="large")

with col1:
    # Verarbeitet die aktuelle Anfrage (Query);
    query_text = st.text_input("", value=q, placeholder="Suchbegriff eingeben")

    enter_triggered = query_text != q and query_text != ""
    button_triggered = st.button("Suchen", type="primary")

    if enter_triggered or button_triggered:
        if query_text:
            # Speichert die Anfrageparameter und lädt die Seite erneut
            st.query_params.update({"q": up.quote(query_text, safe=''), "view": "grid"})
            st.rerun()

    st.markdown("---")
    st.subheader("Filter")


    st.set_page_config(layout="wide")

    # ----- Genres Filter -----
    with open("genres.json", "r", encoding="utf-8") as f:
        GENRE_DATA = json.load(f)

    ALL_GENRE_FILTERS = sorted(
        set(
            g["filter"] for g in GENRE_DATA
        ).union(
            g.get("filter2") for g in GENRE_DATA if g.get("filter2")
        )
    )

    if "selected_genres" not in st.session_state:
        st.session_state.selected_genres = []

    if "master_genres" not in st.session_state:
        st.session_state.master_genres = False

    for f in ALL_GENRE_FILTERS:
        key = f"genre_{f}"
        if key not in st.session_state:
            st.session_state[key] = False


    def toggle_all_genres():
        value = st.session_state.master_genres
        for f in ALL_GENRE_FILTERS:
            st.session_state[f"genre_{f}"] = value

    def update_master_genres():
        all_checked = all(
            st.session_state[f"genre_{f}"] for f in ALL_GENRE_FILTERS
        )
        st.session_state.master_genres = all_checked

    # Checkboxen für Genres
    st.checkbox(
        "Alle Genres auswählen",
        key="master_genres",
        on_change=toggle_all_genres
    )

    with st.expander("Genres", expanded=False):
        selected_genres = []

        for f in ALL_GENRE_FILTERS:
            checked = st.checkbox(
                f,
                key=f"genre_{f}",
                on_change=update_master_genres
            )
            if checked:
                selected_genres.append(f)

        st.session_state.selected_genres = selected_genres


    # ----- Länder Filter -----
    with open("countries.json", "r", encoding="utf-8") as f:
        COUNTRY_DATA = json.load(f)

    ALL_COUNTRY_FILTERS = sorted(
        set(c["filter"] for c in COUNTRY_DATA)
    )

    if "selected_countries" not in st.session_state:
        st.session_state.selected_countries = []

    if "master_countries" not in st.session_state:
        st.session_state.master_countries = False

    for f in ALL_COUNTRY_FILTERS:
        key = f"country_{f}"
        if key not in st.session_state:
            st.session_state[key] = False


    def toggle_all_countries():
        value = st.session_state.master_countries
        for f in ALL_COUNTRY_FILTERS:
            st.session_state[f"country_{f}"] = value

    def update_master_countries():
        all_checked = all(
            st.session_state[f"country_{f}"] for f in ALL_COUNTRY_FILTERS
        )
        st.session_state.master_countries = all_checked


    # Checkboxen für Länder
    st.checkbox(
        "Alle Länder auswählen",
        key="master_countries",
        on_change=toggle_all_countries
    )

    with st.expander("Länder", expanded=False):
        selected_countries = []

        for f in ALL_COUNTRY_FILTERS:
            checked = st.checkbox(
                f,
                key=f"country_{f}",
                on_change=update_master_countries
            )
            if checked:
                selected_countries.append(f)

        st.session_state.selected_countries = selected_countries


    # ----- Bewertungen (Rating) Filter -----
    filter_full_star = "★"

    def render_stars(min_r, max_r):
        if max_r is 0.5:
            return "Keine Bewertung"

        star_count = int(max_r + 0.1)
        return filter_full_star * star_count

    RATING_OPTIONS = [
        (4.5, 5.01),  # 5 Sterne
        (3.5, 4.5),  # 4 Sterne
        (2.5, 3.5),  # 3 Sterne
        (1.5, 2.5),  # 2 Sterne
        (0.5, 1.5),  # 1 Stern
        (0.0, 0.5)  # Keine Bewertung oder 0 Sterne
    ]

    if "selected_ratings" not in st.session_state:
        st.session_state.selected_ratings = []

    if "master_ratings" not in st.session_state:
        st.session_state.master_ratings = False

    for r in RATING_OPTIONS:
        key = f"rating_{r[0]}"
        if key not in st.session_state:
            st.session_state[key] = False


    def toggle_all_ratings():
        value = st.session_state.master_ratings
        for r in RATING_OPTIONS:
            st.session_state[f"rating_{r[0]}"] = value

    def update_master_ratings():
        all_checked = all(
            st.session_state[f"rating_{r[0]}"] for r in RATING_OPTIONS
        )
        st.session_state.master_ratings = all_checked


    # Checkboxen für Bewertungen
    st.checkbox(
        "Alle Bewertungen auswählen",
        key="master_ratings",
        on_change=toggle_all_ratings
    )

    if "selected_ratings" not in st.session_state:
        st.session_state.selected_ratings = []

    with st.expander("Bewertungen", expanded=False):
        selected_ratings = []

        for r in RATING_OPTIONS:
            min_r, max_r = r
            label = render_stars(min_r, max_r)

            checked = st.checkbox(
                label,
                key=f"rating_{min_r}"
            )

            if checked:
                selected_ratings.append(r)

        st.session_state.selected_ratings = selected_ratings



with col2:

    # ----- Detail View -----

    if view == "detail" and selected_id:
        q_t = index.parse_query(selected_id, ["id"])
        detail_hits = searcher.search(q_t, 1).hits
        detail_score, detail_address = detail_hits[0]
        detail_doc = searcher.doc(detail_address)

        detail_title = detail_doc["title"][0]
        detail_overview_src = detail_doc["tmdb_overview"] or detail_doc["description"]
        detail_overview = detail_overview_src[0]
        detail_poster = detail_doc["tmdb_poster_path"]
        detail_poster_url = (TMDB_PATH_SMALL + detail_poster[0]) if detail_poster else ""
        trailer = detail_doc["trailer"]
        video_key = detail_doc["trailer"][0] if trailer else ""

        rating_list = detail_doc["tmdb_vote_average"]
        raw_rating = float(rating_list[0]) if rating_list else 0.0
        rating = raw_rating / 2
        year_list = detail_doc["start"]
        year = str(year_list[0]) if year_list else ""
        countries_list = detail_doc["countries"]
        countries = ", ".join(countries_list) if countries_list else ""
        if countries == "United States of America":
            countries = "USA"
        elif countries == "United Kingdom":
            countries = "UK"


        st.markdown(
            f"<h2 style='margin-bottom: 1em;'>{detail_title}</h2>",
            unsafe_allow_html=True
        )

        rating_5 = raw_rating / 2
        rounded_half = round(rating_5 * 2) / 2

        stars = ""
        for i in range(1, 6):
            if rounded_half >= i:
                stars += full_star
            elif rounded_half + 0.5 == i:
                stars += half_star
            else:
                stars += empty_star


        meta_parts = []

        if stars and rating != 0.0:
            meta_parts.append(f"{stars} &nbsp; {raw_rating:.1f}")

        if year:
            meta_parts.append(year)

        if countries:
            meta_parts.append(countries)

        st.markdown(
            f"<div style='display:inline-flex; align-items:center; gap:8px; margin-bottom:10px;'>"
            f"{' &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp;&nbsp; '.join(meta_parts)}"
            f"</div>",
            unsafe_allow_html=True
        )

        genres = detail_doc["genres"]
        tags_html = "<div>"
        if genres is not None:
            for tag in genres:
                tags_html += f'<span class="tag">{tag}</span>'
            tags_html += "</div>"
        st.markdown(tags_html, unsafe_allow_html=True)

        st.markdown(
            f"<div style='margin-top:16px; margin-bottom:16px;'>{detail_overview}</div>",
            unsafe_allow_html=True
        )

        if video_key != "":
            st.video(f"https://www.youtube.com/watch?v={video_key}")

        if st.button("← Zurück zur Übersicht"):
            st.query_params.update({"view": "grid"})
            st.query_params.pop("id", None)
            st.rerun()
        st.stop()


    # ----- Filter Ergebnisse -----

    selected_genre_filters = st.session_state.get("selected_genres", [])
    selected_country_filters = st.session_state.get("selected_countries", [])
    selected_rating_filters = st.session_state.get("selected_ratings", [])

    if selected_genre_filters or selected_country_filters or selected_rating_filters:

        st.markdown(
            "<h2 style='margin-bottom: 1em;'>Gefilterte Ergebnisse</h2>",
            unsafe_allow_html=True
        )

        hits = searcher.search(Query.all_query(), 1000).hits
        cards_html = ['<div class="grid">']
        match_found = False

        for score, addr in hits:
            doc = searcher.doc(addr)

            doc_id = doc["id"][0]
            title = doc["title"][0]

            poster = doc["tmdb_poster_path"]
            poster_url = (TMDB_PATH_SMALL + poster[0]) if poster else ""

            try:
                doc_genres = doc["genres"]
            except:
                doc_genres = []

            try:
                doc_countries = doc["countries"]
            except:
                doc_countries = []

            try:
                raw_rating = float(doc["tmdb_vote_average"][0])
                rating_5 = raw_rating / 2
            except:
                rating_5 = 0

            genre_match = False
            country_match = False
            rating_match = False

            # Genre Match
            if selected_genre_filters:
                for g in doc_genres:
                    for entry in GENRE_DATA:
                        if entry["tag"].lower() == g.lower():
                            filters = [entry["filter"]]
                            if entry.get("filter2"):
                                filters.append(entry["filter2"])

                            if any(f in selected_genre_filters for f in filters):
                                genre_match = True
                                break
                    if genre_match:
                        break

            # Country Match
            if selected_country_filters:
                for c in doc_countries:
                    for entry in COUNTRY_DATA:
                        if entry["tag"].lower() == c.lower():
                            if entry["filter"] in selected_country_filters:
                                country_match = True
                                break
                    if country_match:
                        break

            # Rating Match
            if selected_rating_filters:
                for min_r, max_r in selected_rating_filters:
                    if min_r <= rating_5 < max_r:
                        rating_match = True
                        break
            else:
                rating_match = True

            # OR-Logik
            matches = True

            if selected_genre_filters and not genre_match:
                matches = False

            if selected_country_filters and not country_match:
                matches = False

            if selected_rating_filters and not rating_match:
                matches = False

            if matches:
                match_found = True

                href = f"?view=detail&id={doc_id}"
                img_tag = f'<img src="{poster_url}" loading="lazy" alt="poster">' if poster_url else ""

                cards_html.append(
                    f'<a class="card" href="{href}" target="_self">{img_tag}<div class="t">{title}</div></a>'
                )

        cards_html.append("</div>")

        if match_found:
            st.markdown("".join(cards_html), unsafe_allow_html=True)
        else:
            st.warning("Keine Serien entsprechen den gewählten Filtern.")

        st.stop()

    # Raster (Grid) darstellen, wenn q existiert
    if q:
        st.markdown(
            f"<h2 style='margin-bottom: 1em;'>Such-Ergebnisse</h2>",
            unsafe_allow_html=True
        )
        unquoted_q = up.unquote(q).lower()
        query = unquoted_q.strip()
        terms = query.split()
        boolean_parts = []
        for term in terms:
            u_q = index.parse_query(term, ["title"])  # uses en_stem for "title"
            boolean_parts.append((Occur.Must, u_q))
        boolean_query = Query.boolean_query(boolean_parts)
        hits = searcher.search(boolean_query, 50).hits

        if not hits:
            st.warning("Keine Ergebnisse gefunden.")
        else:
            # Erstelle das Grid mit klickbaren Thumbnails
            cards_html = ['<div class="grid">']

            for score, addr in hits:
                doc = searcher.doc(addr)
                doc_id = doc["id"][0]
                title = doc["title"][0]
                start = doc["start"][0] if doc["start"] else ""
                poster = doc["tmdb_poster_path"]
                poster_url = (TMDB_PATH_SMALL + poster[0]) if poster else ""
                href = f"?view=detail&id={doc_id}&q={up.quote(q, safe='')}"
                img_tag = f'<img src="{poster_url}" loading="lazy" alt="poster">' if poster_url else ""
                cards_html.append(
                    f"""<a class="card" href="{href}" target="_self">{img_tag}<div class="t">{title}</div></a>""")

            cards_html.append("</div>")
            st.markdown("".join(cards_html), unsafe_allow_html=True)

    else:
        st.markdown(
            "<h1 style='margin-top:-20px;'>Durchstöbern</h1>",
            unsafe_allow_html=True
        )
        st.info("Gib einen Suchbegriff ein oder nutze die Filter, um Serien gezielt einzugrenzen.")