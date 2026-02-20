import urllib.parse as up
from typing import Any
import streamlit as st
from tantivy import Query, Index, SchemaBuilder, Occur
import random
import utils

# Konstanten
TMDB_PATH = "https://image.tmdb.org/t/p/original"
TMDB_PATH_SMALL = "https://image.tmdb.org/t/p/w200"
INDEX_PATH = "serien_300"  # bestehendes Tantivy-Index-Verzeichnis
TOP_K = 20          # wie viele Ergebnisse angezeigt werden sollen

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

full_star = '<i class="fa-solid fa-star"></i>'
half_star = '<i class="fa-solid fa-star-half-stroke"></i>'
empty_star = '<i class="fa-regular fa-star"></i>'


# Hilfsfunktion für Seitenrouting mit Anfrageparametern.
def get_qp() -> dict[str, Any]:
    return getattr(st, "query_params", {})

qp = st.query_params
view = qp.get("view")
selected_id = qp.get("id")
q = qp.get("q", "")


# ----- Detail View -----

@st.dialog("Details")
def show_detail_dialog(detail_doc):
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

    st.title(detail_title)

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
        f"<div style='margin-top:12px; margin-bottom:16px;'>{detail_overview}</div>",
        unsafe_allow_html=True
    )

    if video_key != "":
        st.video(f"https://www.youtube.com/watch?v={video_key}")

    if st.button("Schließen"):
        st.query_params.clear()
        st.rerun()


if view == "detail" and selected_id:
    q_t = index.parse_query(selected_id, ["id"])
    hits = searcher.search(q_t, 1).hits
    if hits:
        _, addr = hits[0]
        detail_doc = searcher.doc(addr)
        show_detail_dialog(detail_doc)



# ----- Hauptseite – Random Cards -----

st.markdown(
    "<h1 style='text-align:center; margin-top:-2em;'>Cineberry - Home</h1>",
    unsafe_allow_html=True
)

all_hits = searcher.search(Query.all_query(), 500).hits

def display_series_cards(hits, title="Serien", limit=12, randomize=False, sort_key=None, reverse=True):

    cards_html = []

    hits_to_show = hits.copy()
    if randomize:
        random.shuffle(hits_to_show)
    elif sort_key:
        hits_to_show = sorted(hits_to_show, key=sort_key, reverse=reverse)

    count = 0
    for score, addr in hits_to_show:
        if count >= limit:
            break

        doc = searcher.doc(addr)
        poster = doc["tmdb_poster_path"]
        if not poster:
            continue

        doc_id = doc["id"][0]
        title_card = doc["title"][0]
        poster_url = TMDB_PATH + poster[0]
        href = f"?view=detail&id={doc_id}&q={up.quote(q, safe='')}"

        img_tag = f'<img src="{poster_url}" loading="lazy" alt="poster">'
        cards_html.append(
            f"""<a class="card" href="{href}" target="_self">{img_tag}<div class="t">{title_card}</div></a>"""
        )

        count += 1

    st.markdown(
        f"<h2 style='font-size:1.5em; padding: 1em 0 0.3em 1em; margin-top:0.5em; border-top:1px solid white'>{title}</h2>",
        unsafe_allow_html=True
    )
    utils.display_random_items(cards_html)

# Zufällige Serien
display_series_cards(all_hits, title="Lass den Zufall entscheiden", limit=12, randomize=True)

# Beliebteste Serien (nach Score)
display_series_cards(all_hits, title="Neueste Serien", limit=12, sort_key=lambda x: float(searcher.doc(x[1])["start"][0]) if searcher.doc(x[1])["start"] else 0)

# Beliebteste Serien (nach Score)
display_series_cards(all_hits, title="Beliebteste Serien", limit=12, sort_key=lambda x: float(searcher.doc(x[1])["tmdb_popularity"][0]) if searcher.doc(x[1])["tmdb_popularity"] else 0)