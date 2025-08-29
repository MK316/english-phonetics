import streamlit as st
import requests
import re

st.set_page_config(page_title="Lecture Slide Player — Chapter 1", layout="wide")
st.title("📚 Lecture Slide Player — Chapter 1")

# ------------ CONFIG ------------
GITHUB_OWNER  = "MK316"
GITHUB_REPO   = "english-phonetics"
GITHUB_BRANCH = "main"
FOLDER_PATH   = "pages/lecture/Ch1"   # your JPEG/PNG folder
VALID_EXTS    = (".png", ".jpg", ".jpeg", ".webp")
DISPLAY_WIDTH = 900  # main slide width in px (adjust to avoid scrolling)
THUMB_MAX     = 10   # how many thumbnails to show
THUMB_COLS    = 10   # columns for thumbnails
# --------------------------------

def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

@st.cache_data(show_spinner=False, ttl=600)
def list_github_images(owner: str, repo: str, folder: str, branch: str):
    api = f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}?ref={branch}"
    r = requests.get(api, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"GitHub API error {r.status_code}. Check owner/repo/branch/path.\n{r.text[:200]}")
    items = r.json()
    files = [it for it in items if it.get("type") == "file" and it["name"].lower().endswith(VALID_EXTS)]
    files.sort(key=lambda x: natural_key(x["name"]))
    raw_base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{folder}"
    urls  = [f"{raw_base}/{f['name']}" for f in files]
    names = [f["name"] for f in files]
    return urls, names

# Load slides
try:
    slides, filenames = list_github_images(GITHUB_OWNER, GITHUB_REPO, FOLDER_PATH, GITHUB_BRANCH)
except Exception as e:
    st.error(f"Failed to load images: {e}")
    st.stop()

if not slides:
    st.warning("No image files found in the folder.")
    st.stop()

# Session state
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0

def clamp(i: int) -> int:
    return max(0, min(len(slides) - 1, i))

# ===== Sidebar controls (always visible on the left) =====
with st.sidebar:
    st.subheader("Controls")
    # Prev / Next buttons
    if st.button("⬅️ Previous", use_container_width=True, key="prev_btn"):
        st.session_state.slide_idx = clamp(st.session_state.slide_idx - 1)

    # Jump to slide (label kept for accessibility)
    cur = st.session_state.slide_idx + 1
    jump = st.number_input(
        "Jump to slide",
        min_value=1,
        max_value=len(slides),
        value=cur,
        step=1,
        key="jump_num",
    )
    if jump != cur:
        st.session_state.slide_idx = int(jump) - 1

    if st.button("Next ➡️", use_container_width=True, key="next_btn"):
        st.session_state.slide_idx = clamp(st.session_state.slide_idx + 1)

    # Optional: quick width tweak so it fits without scrolling on different screens
    DISPLAY_WIDTH = st.slider("Slide width (px)", 700, 1100, DISPLAY_WIDTH, step=50)

# st.divider()

# ===== Main area: slide + thumbnails =====
idx = st.session_state.slide_idx
st.image(slides[idx], width=DISPLAY_WIDTH, caption=f"Slide {idx + 1}")
st.markdown(f"**Slide {idx + 1} / {len(slides)}** — *{filenames[idx]}*")
with st.expander("Thumbnails"):
    n = min(THUMB_MAX, len(slides))
    cols = st.columns(THUMB_COLS if n >= THUMB_COLS else n)
    thumb_width = int(DISPLAY_WIDTH / THUMB_COLS) if THUMB_COLS else 120
    for i in range(n):
        col = cols[i % len(cols)]
        with col:
            if st.button(f"{i+1}", key=f"thumb_{i}", use_container_width=True):
                st.session_state.slide_idx = i
            col.image(slides[i], width=thumb_width)
