import streamlit as st
import requests
import random

# ==========================================
# 1. CONFIGURATION
# ==========================================
st.set_page_config(page_title="NeuralStream", page_icon="🍿", layout="wide", initial_sidebar_state="collapsed")

# Initialize Session State
if 'my_list' not in st.session_state: st.session_state.my_list = []
if 'selected_movie' not in st.session_state: st.session_state.selected_movie = None
if 'page' not in st.session_state: st.session_state.page = "Home"

API_URL = "https://NeuralStream.onrender.com"

# ==========================================
# 2. CSS STYLING (NETFLIX DARK THEME)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Inter:wght@400;600&display=swap');

    /* APP BACKGROUND */
    .stApp { background-color: #000000; color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* REMOVE WHITESPACE */
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }

    /* HEADERS */
    h1, h2, h3 { font-family: 'Bebas Neue', sans-serif; letter-spacing: 1.5px; color: #E50914 !important; }
    
    /* --- BUTTONS: HIGH CONTRAST (WHITE & BLACK) --- */
    
    /* Target ALL buttons inside columns (The Grid Buttons) */
    div[data-testid="column"] button {
        background-color: #ffffff !important; /* White Background */
        color: #000000 !important;            /* Black Text */
        border: 1px solid #000000 !important; /* Black Border */
        border-radius: 4px !important;
        font-size: 13px !important;
        padding: 4px 8px !important;
        min-height: 0px !important;
        height: auto !important;
        line-height: 1.2 !important;
        transition: all 0.2s ease-in-out;
        width: 100%;
        font-weight: 700 !important;
    }

    /* Hover Effect */
    div[data-testid="column"] button:hover {
        background-color: #e6e6e6 !important; /* Light Grey Hover */
        border-color: #E50914 !important;     /* Red Border */
        color: #E50914 !important;            /* Red Text */
        transform: scale(1.02);
    }
    
    /* EXCEPTION: Primary Buttons (Like 'Play Trailer') should be Bright */
    button[kind="primary"] {
        background-color: #E50914 !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 16px !important;
        padding: 10px 20px !important;
        height: auto !important;
    }
    button[kind="primary"]:hover {
        background-color: #ff0f1f !important;
    }

    /* MOVIE CARDS */
    .poster-img {
        border-radius: 4px;
        transition: transform 0.3s;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .poster-img:hover {
        transform: scale(1.05);
        cursor: pointer;
        z-index: 10;
        box-shadow: 0 10px 20px rgba(0,0,0,0.8);
    }
    
    /* TEXT STYLING */
    .movie-title {
        font-weight: 600;
        font-size: 0.9rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        margin-top: 8px;
        color: #ddd;
    }
    .meta-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
        font-size: 0.75rem;
        color: #888;
    }
    .match-score { color: #46d369; font-weight: bold; }
    
    /* DETAILS PANEL */
    .glass-panel {
        background: rgba(20, 20, 20, 0.95);
        border-radius: 12px;
        padding: 30px;
        border: 1px solid #333;
        margin-top: -80px;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_image_url(poster_path, title):
    if poster_path and len(str(poster_path)) > 5:
        return f"https://image.tmdb.org/t/p/w500/{str(poster_path).lstrip('/')}"
    return f"https://placehold.co/300x450/222/FFF/png?text={title.replace(' ', '+')}"

def add_to_list(movie):
    titles = [m['title'] for m in st.session_state.my_list]
    if movie['title'] not in titles:
        st.session_state.my_list.append(movie)
        st.toast(f"✅ Added {movie['title']}")
    else:
        st.toast(f"⚠️ Already saved")

def nav_to(page, movie=None):
    st.session_state.page = page
    if movie: st.session_state.selected_movie = movie
    st.rerun()

def go_home():
    st.session_state.page = "Home"
    st.rerun()

# ==========================================
# 4. COMPONENT: MOVIE ROW
# ==========================================
def render_movie_row(title, movies):
    if not movies: return
    st.markdown(f"### {title}")
    
    # 5 Movies Per Row
    cols = st.columns(5)
    
    for i, m in enumerate(movies[:5]):
        img_url = get_image_url(m.get('poster_path'), m.get('title'))
        
        # Format Rating
        rating = str(m.get('rating', '95'))
        if "%" not in rating: rating += "% Match"
        
        with cols[i]:
            # 1. Poster Image
            st.markdown(f"""
            <img src="{img_url}" class="poster-img" style="width:100%; aspect-ratio: 2/3; object-fit: cover;">
            <div class="movie-title">{m.get('title')}</div>
            <div class="meta-row">
                <span class="match-score">{rating}</span>
                <span style="border:1px solid #555; padding:0 3px; border-radius:2px; font-size:9px;">HD</span>
            </div>
            """, unsafe_allow_html=True)
            
            # 2. Buttons (Now perfectly aligned)
            # Use 'gap' to remove whitespace between buttons
            c1, c2 = st.columns([1, 1], gap="small")
            
            # Unique keys prevent "wrong movie" bug
            unique_key = f"{title.replace(' ', '')}_{i}_{m['title'].replace(' ', '')}"
            
            with c1:
                st.button("▼ Info", key=f"inf_{unique_key}", on_click=nav_to, args=("Details", m))
            
            with c2:
                st.button("✚ Add", key=f"add_{unique_key}", on_click=add_to_list, args=(m,))

# ==========================================
# 5. COMPONENT: DETAILS PAGE
# ==========================================
def render_details():
    m = st.session_state.selected_movie
    if not m: 
        go_home()
        return
    
    poster = get_image_url(m.get('poster_path'), m.get('title'))
    backdrop = poster.replace("w500", "original")
    
    # Back Button
    st.button("⬅ BACK TO BROWSE", on_click=go_home)

    # Background Overlay
    st.markdown(f"""
    <div style="
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(to right, #000 10%, transparent 90%), url('{backdrop}');
        background-size: cover; background-position: center; z-index: -1; opacity: 0.3;">
    </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns([1.5, 3])
    
    with c1:
        st.image(poster, use_container_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Play Trailer Button
        yt_url = f"https://www.youtube.com/results?search_query={m.get('title')}+trailer"
        st.link_button("▶ PLAY TRAILER", yt_url, type="primary", use_container_width=True)
            
    with c2:
        # Title
        st.markdown(f"""
        <h1 style="font-size: 4rem; margin: 0; line-height: 1;">{m.get('title')}</h1>
        """, unsafe_allow_html=True)
        
        # Meta Data
        rating = str(m.get('rating', '95'))
        if "%" not in rating: rating += "% Match"
        
        st.markdown(f"""
        <div style="display:flex; align-items:center; gap: 15px; margin: 15px 0; color: #ccc;">
            <span style="color:#46d369; font-weight:bold; font-size:1.1rem;">{rating}</span>
            <span style="border: 1px solid #555; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem;">2024</span>
            <span style="border: 1px solid #555; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem;">4K</span>
            <span style="font-size: 0.9rem;">{m.get('genre', 'Action')}</span>
        </div>
        <p style="font-size: 1.1rem; line-height: 1.6; color: #ddd; max-width: 800px;">
            {m.get('overview', 'Plot unavailable. Experience this trending title now.')}
        </p>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("✚ Add to My List", key="big_add_btn", on_click=add_to_list, args=(m,))

# ==========================================
# 6. MAIN APP LOGIC
# ==========================================

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg", width=140)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Navigation
    if st.button("🏠 Home"): nav_to("Home")
    if st.button("🔍 Explore"): nav_to("Explore")
    if st.button("📋 My List"): nav_to("My List")
    
    st.markdown("---")
    user_name = st.text_input("Profile Name", "Guest")

# Page Routing
if st.session_state.page == "Home":
    
    # 1. Fetch Data
    try:
        rec = requests.post(f"{API_URL}/recommend", json={"user_id": "42"}).json().get("movies", [])
        act = requests.post(f"{API_URL}/search", json={"query": "", "genre": "Action"}).json().get("results", [])
        sci = requests.post(f"{API_URL}/search", json={"query": "", "genre": "Sci-Fi"}).json().get("results", [])
    except: 
        rec, act, sci = [], [], []

    # 2. Dynamic Hero
    hero_movie = random.choice(rec) if rec else {"title": "Loading...", "overview": "Please wait."}
    backdrop = get_image_url(hero_movie.get('poster_path'), "").replace("w500", "original")
    
    st.markdown(f"""
    <div style="
        padding: 60px; border-radius: 12px; margin-bottom: 40px;
        background: linear-gradient(to right, #000 40%, transparent), url('{backdrop}');
        background-size: cover; background-position: center 20%; 
        box-shadow: inset 0 0 80px #000; border: 1px solid #333;
    ">
        <h1 style="font-size: 4rem; text-shadow: 2px 2px 10px black; margin: 0;">{hero_movie.get('title')}</h1>
        <p style="font-size: 1.2rem; max-width: 500px; text-shadow: 2px 2px 4px black; color: #ddd; margin-top: 10px;">
            {hero_movie.get('overview', '')[:150]}...
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 3. Dynamic Header
    if user_name.lower() != "guest":
        st.markdown(f"### 👤 Top Picks for {user_name}")
    else:
        st.markdown(f"### 🔥 Trending Now")
    
    render_movie_row("", rec) 
    render_movie_row("🔫 High-Octane Action", act)
    render_movie_row("🚀 Sci-Fi Universes", sci)

elif st.session_state.page == "Explore":
    st.markdown("## 🔍 Explore")
    c1, c2 = st.columns([3,1])
    q = c1.text_input("Search")
    g = c2.selectbox("Genre", ["All", "Action", "Sci-Fi", "Comedy", "Horror", "Animation"])
    
    if q or g != "All":
        try:
            res = requests.post(f"{API_URL}/search", json={"query": q, "genre": g}).json().get("results", [])
            render_movie_row("Results", res)
        except: st.error("Search Failed")

elif st.session_state.page == "My List":
    st.markdown("## 📋 My Watchlist")
    if st.session_state.my_list:
        render_movie_row("Saved Movies", st.session_state.my_list)
        if st.button("Clear List"):
            st.session_state.my_list = []
            st.rerun()
    else:
        st.info("List is empty")

elif st.session_state.page == "Details":
    render_details()
