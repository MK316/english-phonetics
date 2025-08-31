import streamlit as st
import requests
import re

st.set_page_config(page_title="Lecture Slide Player — Chapter 1", layout="wide")
st.header("📚 Chapter 1: Articulation and acoustics")

# ------------ CONFIG ------------
GITHUB_OWNER  = "MK316"
GITHUB_REPO   = "english-phonetics"
GITHUB_BRANCH = "main"
FOLDER_PATH   = "pages/lecture/Ch01"
VALID_EXTS    = (".png", ".jpg", ".jpeg", ".webp")
DISPLAY_WIDTH_DEFAULT = 900
THUMB_MAX, THUMB_COLS = 20, 10
# ---------------------------------

def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

@st.cache_data(show_spinner=False, ttl=600)
def list_all_github_images(owner: str, repo: str, folder: str, branch: str):
    """Handles GitHub API pagination to get all files in a folder"""
    files = []
    page = 1
    while True:
        api = f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}?ref={branch}&per_page=100&page={page}"
        r = requests.get(api, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"GitHub API error {r.status_code}. Check owner/repo/branch/path.\n{r.text[:200]}")
        batch = r.json()
        if not batch:
            break
        files.extend(batch)
        page += 1

    valid_files = [it for it in files if it.get("type") == "file" and it["name"].lower().endswith(VALID_EXTS)]
    valid_files.sort(key=lambda x: natural_key(x["name"]))
    raw_base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{folder}"
    urls = [f"{raw_base}/{f['name']}" for f in valid_files]
    names = [f["name"] for f in valid_files]
    return urls, names

# Load all slide images
slides, filenames = list_all_github_images(GITHUB_OWNER, GITHUB_REPO, FOLDER_PATH, GITHUB_BRANCH)
if not slides:
    st.warning("No image files found in the folder.")
    st.stop()

# ---- Session State Initialization ----
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0

# ===== Functions =====
def clamp(i: int) -> int:
    return max(0, min(len(slides) - 1, i))

def sync_from_jump():
    st.session_state.slide_idx = clamp(int(st.session_state.jump_num) - 1)

# ===== Sidebar Controls =====
with st.sidebar:
    st.subheader("Controls")
    st.number_input(
        "Jump to slide",
        min_value=1,
        max_value=len(slides),
        step=1,
        key="jump_num",  # Keep key only, no value
        on_change=sync_from_jump,
    )
    display_width = st.slider("Slide width (px)", 700, 1100, DISPLAY_WIDTH_DEFAULT, step=50)

# ===== Keep jump_num synced with current slide index =====
# (only if not just triggered by sidebar input)
if "jump_num" not in st.session_state or st.session_state.jump_num != st.session_state.slide_idx + 1:
    st.session_state.jump_num = st.session_state.slide_idx + 1

# ===== Main Display Area =====
idx = st.session_state.slide_idx
st.image(slides[idx], width=display_width, caption=f"Slide {idx + 1} / {len(slides)}")

# ===== Thumbnails =====
with st.expander("Thumbnails"):
    n = min(THUMB_MAX, len(slides))
    cols = st.columns(THUMB_COLS if n >= THUMB_COLS else n)
    thumb_width = int(display_width / THUMB_COLS) if THUMB_COLS else 120

    for i in range(n):
        col = cols[i % len(cols)]
        with col:
            if st.button(f"{i+1}", key=f"thumb_{i}", use_container_width=True):
                st.session_state.slide_idx = i  # update immediately
            col.image(slides[i], width=thumb_width)
