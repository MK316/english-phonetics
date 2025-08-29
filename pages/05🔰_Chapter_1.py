import streamlit as st
import requests
import re

st.set_page_config(page_title="Lecture Slide Player — Chapter 1", layout="wide")
st.title("📚 Lecture Slide Player — Chapter 1")

# ------------ CONFIG ------------
GITHUB_OWNER  = "MK316"
GITHUB_REPO   = "english-phonetics"
GITHUB_BRANCH = "main"
FOLDER_PATH   = "pages/lecture/Ch1"   # your folder with JPEG/PNG slides
VALID_EXTS    = (".png", ".jpg", ".jpeg", ".webp")

# How wide to show the main slide (px). Tweak this if your users have smaller screens.
DISPLAY_WIDTH = 900

# How many thumbnails to show and their columns
THUMB_MAX = 10
THUMB_COLS = 10
# --------------------------------

# Small CSS to tighten spacing a bit
st.markdown("""
<style>
/* tighten top margin on number input label */
div[data-testid="stNumberInput"] label { margin-bottom: 0.25rem !important; }
</style>
""", unsafe_allow_html=True)


def natural_key(s: str):
    """Natural sort: slide_2 before slide_10."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


@st.cache_data(show_spinner=False, ttl=600)
def list_github_images(owner: str, repo: str, folder: str, branch: str):
    """Return naturally-sorted RAW URLs + filenames for images in a GitHub folder."""
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


# Load slide list
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


# ===== Controls row (aligned) =====
c1, c2, c3 = st.columns([1, 2, 1], vertical_alignment="center")

with c1:
    st.markdown("**Previous**")
    if st.button("⬅️ Previous", use_container_width=True):
        st.session_state.slide_idx = clamp(st.session_state.slide_idx - 1)

with c3:
    st.markdown("**Next**")
    if st.button("Next ➡️", use_container_width=True):
        st.session_state.slide_idx = clamp(st.session_state.slide_idx + 1)

with c2:
    st.markdown("**Jump to slide**")
    cur = st.session_state.slide_idx + 1
    jump = st.number_input(
        label="",              # no label inside the widget
        min_value=1,
        max_value=len(slides),
        value=cur,
        step=1                 # <-- removed `help=...` to kill the "?"
    )
    if jump != cur:
        st.session_state.slide_idx = int(jump) - 1


st.divider()

# ===== Display current slide (smaller to avoid scrolling) =====
idx = st.session_state.slide_idx
st.markdown(f"**Slide {idx + 1} / {len(slides)}** — *{filenames[idx]}*")
st.image(slides[idx], width=DISPLAY_WIDTH, caption=f"Slide {idx + 1}")

# ===== Thumbnails (smaller) =====
with st.expander("Thumbnails"):
    n = min(THUMB_MAX, len(slides))
    cols = st.columns(THUMB_COLS if n >= THUMB_COLS else n)
    for i in range(n):
        col = cols[i % len(cols)]
        with col:
            if st.button(f"{i+1}", key=f"thumb_{i}", use_container_width=True):
                st.session_state.slide_idx = i
            # Smaller thumbnail width so a row fits nicely
            thumb_width = int(DISPLAY_WIDTH / THUMB_COLS) if THUMB_COLS else 120
            col.image(slides[i], width=thumb_width)
