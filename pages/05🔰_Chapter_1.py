import re
import requests
import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="Lecture Slide Player - Chapter 1", layout="wide")
st.header("Chapter 1: Articulation and Acoustics")

# ------------ CONFIG (edit as needed) ------------
GITHUB_OWNER  = "MK316"
GITHUB_REPO   = "english-phonetics"
GITHUB_BRANCH = "main"
FOLDER_PATH   = "pages/lecture/Ch01"   # path inside the repo

# Confirmed filenames like: F25_Ch01.001.png, F25_Ch01.002.png, ...
FILENAME_PREFIX = "F25_Ch01."
FILENAME_EXT    = ".png"
START_INDEX     = 1
END_INDEX       = 300          # upper bound to probe; set to your max (e.g., 120)

DISPLAY_WIDTH_DEFAULT = 900
THUMB_MAX, THUMB_COLS = 20, 10
TIMEOUT = 8  # seconds for HTTP checks
# --------------------------------------------------

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{FOLDER_PATH}"

def natural_key(s: str):
    # human sort: slide2 before slide10
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def _exists(url: str) -> bool:
    try:
        r = requests.head(url, timeout=TIMEOUT)
        if r.status_code == 405:  # if HEAD blocked, try lightweight GET
            r = requests.get(url, stream=True, timeout=TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False

@st.cache_data(show_spinner=False, ttl=600)
def discover_pngs_by_pattern(raw_base: str, prefix: str, ext: str, start_i: int, end_i: int):
    """Probe F25_Ch01.{i:03d}.png under the raw GitHub folder (no GitHub API)."""
    found = []
    for i in range(start_i, end_i + 1):
        name = f"{prefix}{i:03d}{ext}"   # e.g., F25_Ch01.001.png
        url  = f"{raw_base}/{name}"
        if _exists(url):
            found.append((name, url))

    found.sort(key=lambda x: natural_key(x[0]))
    names = [n for n, _ in found]
    urls  = [u for _, u in found]
    return urls, names

# ---------- Discover slides ----------
slides, filenames = discover_pngs_by_pattern(
    RAW_BASE, FILENAME_PREFIX, FILENAME_EXT, START_INDEX, END_INDEX
)

if not slides:
    st.error(
        "No PNG files discovered with the pattern F25_Ch01.{i:03d}.png.\n"
        "• Verify the folder path and filename pattern.\n"
        "• If your files stop at a smaller number (e.g., 088), set END_INDEX accordingly."
    )
    st.stop()

# ---- Session state init ----
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0
if "jump_num" not in st.session_state:
    st.session_state.jump_num = st.session_state.slide_idx + 1
if "pending_jump" not in st.session_state:
    st.session_state.pending_jump = False  # set True after thumbnail click

def clamp(i: int) -> int:
    return max(0, min(len(slides) - 1, i))

# --- IMPORTANT: if a thumbnail was clicked in the previous run,
# sync the number_input value BEFORE rendering the widget this run.
if st.session_state.pending_jump:
    st.session_state.jump_num = st.session_state.slide_idx + 1
    st.session_state.pending_jump = False  # consumed

def on_jump_change():
    st.session_state.slide_idx = clamp(int(st.session_state.jump_num) - 1)

# ===== Sidebar controls =====
with st.sidebar:
    st.subheader("Controls")
    # Do not pass value= when using key; avoids overwriting state
    st.number_input(
        "Jump to slide",
        min_value=1,
        max_value=len(slides),
        step=1,
        key="jump_num",
        on_change=on_jump_change,
    )
    display_width = st.slider("Slide width (px)", 700, 1100, DISPLAY_WIDTH_DEFAULT, step=50)

# ===== Main area: slide + caption =====
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
                # Update the source-of-truth index
                st.session_state.slide_idx = i
                # Request that the jump widget be updated on the next run (before render)
                st.session_state.pending_jump = True
            col.image(slides[i], width=thumb_width)
