import streamlit as st
import requests
import re

# === CONFIG ===
GITHUB_USER = "MK316"
GITHUB_REPO = "english-phonetics"
BRANCH = "main"
FOLDER_PATH = "pages/lecture/Ch01"
RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/{FOLDER_PATH}"
HTML_BASE = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/tree/{BRANCH}/{FOLDER_PATH}"
VALID_EXT = ".PNG"
THUMB_MAX, THUMB_COLS = 20, 10
DISPLAY_WIDTH_DEFAULT = 900

# === PAGE SETUP ===
st.set_page_config(page_title="Lecture Slide Viewer", layout="wide")
st.header("📚 Chapter 1: Articulation and Acoustics")

@st.cache_data(ttl=600)
def get_png_files_from_github_html():
    r = requests.get(HTML_BASE)
    if r.status_code != 200:
        raise RuntimeError(f"Failed to load GitHub folder HTML: {r.status_code}")

    # Find all .png links in the folder HTML
    matches = re.findall(r'href=".*?/' + re.escape(FOLDER_PATH) + r'/([^"]+\.png)"', r.text, re.IGNORECASE)
    
    # If still empty, fallback: match any .png link (safer)
    if not matches:
        matches = re.findall(r'href="[^"]+?/([^"/]+\.png)"', r.text, re.IGNORECASE)

    filenames = sorted(set(matches), key=lambda x: [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', x)])
    urls = [f"{RAW_BASE}/{name}" for name in filenames]
    return urls, filenames


# === Load images ===
try:
    slides, filenames = get_png_files_from_github_html()
except Exception as e:
    st.error(f"❌ Could not load images.\n\n{e}")
    st.stop()

if not slides:
    st.warning("No .png files found in the GitHub folder.")
    st.stop()

# === SESSION STATE INIT ===
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0

def clamp(i: int) -> int:
    return max(0, min(len(slides) - 1, i))

def sync_from_jump():
    st.session_state.slide_idx = clamp(int(st.session_state.jump_num) - 1)

# === SIDEBAR ===
with st.sidebar:
    st.subheader("Controls")
    st.number_input(
        "Jump to slide",
        min_value=1,
        max_value=len(slides),
        step=1,
        key="jump_num",
        on_change=sync_from_jump,
    )
    display_width = st.slider("Slide width (px)", 700, 1100, DISPLAY_WIDTH_DEFAULT, step=50)

# === Sync jump_num with slide_idx
if "jump_num" not in st.session_state or st.session_state.jump_num != st.session_state.slide_idx + 1:
    st.session_state.jump_num = st.session_state.slide_idx + 1

# === MAIN DISPLAY ===
idx = st.session_state.slide_idx
st.image(slides[idx], width=display_width, caption=f"Slide {idx + 1} / {len(slides)}")

# === THUMBNAILS ===
with st.expander("Thumbnails"):
    n = min(THUMB_MAX, len(slides))
    cols = st.columns(THUMB_COLS if n >= THUMB_COLS else n)
    thumb_width = int(display_width / THUMB_COLS) if THUMB_COLS else 120

    for i in range(n):
        col = cols[i % len(cols)]
        with col:
            if st.button(f"{i+1}", key=f"thumb_{i}", use_container_width=True):
                st.session_state.slide_idx = i
            col.image(slides[i], width=thumb_width)
