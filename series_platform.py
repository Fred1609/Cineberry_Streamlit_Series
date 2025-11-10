import urllib.parse as up
from typing import Any
import streamlit as st
from tantivy import Query, Index, SchemaBuilder

# Konstanten
TMDB_PATH = "https://image.tmdb.org/t/p/original"
TMDB_PATH_SMALL = "https://image.tmdb.org/t/p/w200"
INDEX_PATH = "neu"  # bestehendes Tantivy-Index-Verzeichnis
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
index_path = "neu"
index = Index(schema, path=str(index_path))
searcher = index.searcher()


# Hilfsfunktion für Seitenrouting mit Anfrageparametern.
# Gibt die Query-Parameter der aktuellen Seite als Dictionary zurück.
# Falls `st.query_params` nicht verfügbar ist, wird ein leeres Dictionary zurückgegeben.
def get_qp() -> dict[str, Any]:
    return getattr(st, "query_params", {})


# (Letzte) Nutzeranfrage, die in den Session-Parametern gespeichert ist
q = get_qp().get("q", "")

# Hauptseite
st.title("TV-Serien")

# Verarbeitet die aktuelle Anfrage (Query);
query_text = st.text_input("Suchbegriff eingeben", value=q, placeholder="z. B. Breaking Bad, Dark, etc. ...")
if st.button("Suchen", type="primary"):
    if not query_text:
        st.info("Bitte gib einen Suchbegriff ein.")
    else:
        # Speichert die Anfrageparameter und lädt die Seite erneut
        st.query_params.update({"q": up.quote(query_text, safe=''), "view": "grid"})
        st.rerun()

# Raster (Grid) darstellen, wenn q existiert
if q:
    query = Query.term_query(schema, "title", q)
    hits = searcher.search(query, TOP_K).hits

    if not hits:
        st.warning("Keine Ergebnisse gefunden.")
    else:
        st.subheader("Ergebnisse")
        # Erstelle das Grid mit klickbaren Thumbnails
        cards_html = ['<div class="grid">']

        for score, addr in hits:
            doc = searcher.doc(addr)
            doc_id = doc["id"][0]
            title = doc["title"][0]
            poster = doc["tmdb_poster_path"]
            poster_url = (TMDB_PATH_SMALL + poster[0]) if poster else ""
            href = ""
            img_tag = f'<img src="{poster_url}" loading="lazy" alt="poster">' if poster_url else ""
            cards_html.append(f'<a class="card" href="{href}">{img_tag}<div class="t">{title}</div></a>')
        cards_html.append("</div>")
        st.markdown("".join(cards_html), unsafe_allow_html=True)
else:
    st.info("Gib einen Suchbegriff ein und klicke auf **Suchen** (oder drücke Enter).")
