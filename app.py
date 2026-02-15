import os
import requests
import streamlit as st

# =============================
# CONFIG
# =============================
API_BASE =  "https://movie-recommendation-vzh6.onrender.com" or "http://127.0.0.1:8000"

TMDB_IMG = "https://image.tmdb.org/t/p/w500"

st.set_page_config(
    page_title="Movie Recommender",
    page_icon="🎬",
    layout="wide",
)

# =============================
# CINEMATIC DARK + GLASS UI
# =============================
st.markdown(
    """
<style>
html, body, [class*="css"]  {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: #ffffff !important;
}

section[data-testid="stSidebar"] {
    background: rgba(0,0,0,0.45) !important;
}

.movie-card {
    position: relative;
    backdrop-filter: blur(18px);
    background: rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 10px;
    border: 1px solid rgba(255,255,255,0.15);
    transition: all 0.3s ease;
}

.movie-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 15px 35px rgba(0,0,0,0.6);
}

.rating-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(255, 215, 0, 0.95);
    color: black;
    font-weight: 700;
    font-size: 0.75rem;
    padding: 4px 8px;
    border-radius: 12px;
}

.movie-title {
    font-size: 0.9rem;
    text-align: center;
    margin-top: 6px;
    font-weight: 500;
}

.stButton>button {
    border-radius: 12px;
    background: linear-gradient(45deg, #00c6ff, #0072ff);
    color: white;
    border: none;
}

.stButton>button:hover {
    background: linear-gradient(45deg, #0072ff, #00c6ff);
}
</style>
""",
    unsafe_allow_html=True,
)

# =============================
# SESSION STATE
# =============================
if "view" not in st.session_state:
    st.session_state.view = "home"

if "selected_tmdb_id" not in st.session_state:
    st.session_state.selected_tmdb_id = None


def goto_home():
    st.session_state.view = "home"
    st.session_state.selected_tmdb_id = None
    st.rerun()


def goto_details(tmdb_id):
    st.session_state.view = "details"
    st.session_state.selected_tmdb_id = tmdb_id
    st.rerun()


# =============================
# API HELPER
# =============================
@st.cache_data(ttl=30)
def api_get_json(path, params=None):
    try:
        r = requests.get(f"{API_BASE}{path}", params=params, timeout=25)
        if r.status_code >= 400:
            return None
        return r.json()
    except Exception:
        return None


# =============================
# POSTER GRID
# =============================
def poster_grid(cards, cols=6, key_prefix="grid"):
    if not cards:
        st.info("No movies found.")
        return

    rows = (len(cards) + cols - 1) // cols
    idx = 0

    for _ in range(rows):
        colset = st.columns(cols)

        for c in range(cols):
            if idx >= len(cards):
                break

            movie = cards[idx]
            idx += 1

            tmdb_id = movie.get("tmdb_id")
            title = movie.get("title", "")
            poster = movie.get("poster_url")
            rating = movie.get("vote_average")

            with colset[c]:
                st.markdown('<div class="movie-card">', unsafe_allow_html=True)

                if poster:
                    st.image(poster, use_container_width=True)

                if rating:
                    st.markdown(
                        f'<div class="rating-badge">⭐ {round(rating,1)}</div>',
                        unsafe_allow_html=True,
                    )

                if st.button("Open", key=f"{key_prefix}_{idx}_{tmdb_id}"):
                    goto_details(tmdb_id)

                st.markdown(
                    f'<div class="movie-title">{title}</div>',
                    unsafe_allow_html=True,
                )

                st.markdown("</div>", unsafe_allow_html=True)


# =============================
# SIDEBAR
# =============================
with st.sidebar:
    st.markdown("## 🎬 Movie Menu")

    if st.button("🏠 Home"):
        goto_home()

    st.markdown("---")

    home_category = st.selectbox(
        "Home Feed",
        ["trending", "popular", "top_rated", "now_playing", "upcoming"],
    )

    grid_cols = st.slider("Grid Columns", 4, 8, 6)


# =============================
# HEADER
# =============================
st.title("🎬 Movie Recommender")
st.caption("Search → Explore → Discover Similar Movies")
st.divider()


# =============================
# HOME VIEW
# =============================
if st.session_state.view == "home":

    typed = st.text_input("Search movie by title")

    if typed.strip() and len(typed.strip()) >= 2:

        with st.spinner("Searching... 🎥"):
            data = api_get_json("/tmdb/search", {"query": typed.strip()})

        if data:
            results = data.get("results", [])

            cards = [
                {
                    "tmdb_id": m["id"],
                    "title": m.get("title"),
                    "poster_url": f"{TMDB_IMG}{m['poster_path']}"
                    if m.get("poster_path")
                    else None,
                    "vote_average": m.get("vote_average"),
                }
                for m in results
            ]

            poster_grid(cards, cols=grid_cols, key_prefix="search")

        else:
            st.error("Search failed.")

        st.stop()

    # HOME FEED
    st.subheader(f"🔥 {home_category.title()} Movies")

    with st.spinner("Loading movies... 🍿"):
        home_cards = api_get_json(
            "/home", {"category": home_category, "limit": 24}
        )

    if home_cards:
        poster_grid(home_cards, cols=grid_cols, key_prefix="home")
    else:
        st.error("Failed to load home feed.")


# =============================
# DETAILS VIEW
# =============================
elif st.session_state.view == "details":

    tmdb_id = st.session_state.selected_tmdb_id

    with st.spinner("Loading movie details... 🎬"):
        details = api_get_json(f"/movie/id/{tmdb_id}")

    if not details:
        st.error("Could not load details.")
        st.stop()

    col1, col2 = st.columns([1, 2.2])

    with col1:
        if details.get("poster_url"):
            st.image(details["poster_url"], use_container_width=True)

    with col2:
        st.header(details.get("title"))
        st.write(details.get("overview"))

    st.divider()
    st.subheader("✨ Recommendations")

    with st.spinner("Finding similar movies... 🎯"):
        bundle = api_get_json(
            "/movie/search",
            {
                "query": details.get("title"),
                "tfidf_top_n": 12,
                "genre_limit": 12,
            },
        )

    if bundle:
        tfidf_cards = [
            x["tmdb"]
            for x in bundle.get("tfidf_recommendations", [])
            if x.get("tmdb")
        ]

        poster_grid(tfidf_cards, cols=grid_cols, key_prefix="tfidf")
        poster_grid(
            bundle.get("genre_recommendations", []),
            cols=grid_cols,
            key_prefix="genre",
        )
    else:
        st.info("No recommendations available.")
