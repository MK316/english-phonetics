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
slides, filenames = list_github_images(GITHUB_OWNER, GITHUB_REPO, FOLDER_PATH, GITHUB_BRANCH)
if not slides:
    st.warning("No image files found in the folder."); st.stop()

# ---- Session state ----
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0
if "jump_num" not in st.session_state:
    st.session_state.jump_num = 1  # 1-based for humans
if "last_idx_for_jump" not in st.session_state:
    st.session_state.last_idx_for_jump = -1

def clamp(i: int) -> int:
    return max(0, min(len(slides) - 1, i))

def sync_from_jump():
    """When the number input changes, update slide_idx immediately."""
    st.session_state.slide_idx = clamp(int(st.session_state.jump_num) - 1)
    st.session_state.last_idx_for_jump = st.session_state.slide_idx

# --- IMPORTANT: keep jump_num in sync BEFORE rendering the widget ---
if st.session_state.last_idx_for_jump != st.session_state.slide_idx:
    st.session_state.jump_num = st.session_state.slide_idx + 1
    st.session_state.last_idx_for_jump = st.session_state.slide_idx

# ===== Sidebar controls =====
with st.sidebar:
    st.subheader("Controls")
    st.number_input(
        "Jump to slide",
        min_value=1,
        max_value=len(slides),
        step=1,
        key="jump_num",
        on_change=sync_from_jump,   # single click on +/- works
    )
    display_width = st.slider("Slide width (px)", 700, 1100, DISPLAY_WIDTH_DEFAULT, step=50)

# st.divider()

# ===== Main area: slide + caption =====
idx = st.session_state.slide_idx
st.image(slides[idx], width=display_width, caption=f"Slide {idx + 1} / {len(slides)}")

# === Create a shadow state for jump_num to avoid direct conflict with the widget ===
if "manual_jump_num" not in st.session_state:
    st.session_state.manual_jump_num = st.session_state.jump_num

with st.expander("Thumbnails"):
    n = min(THUMB_MAX, len(slides))
    cols = st.columns(THUMB_COLS if n >= THUMB_COLS else n)
    thumb_width = int(display_width / THUMB_COLS) if THUMB_COLS else 120

    for i in range(n):
        col = cols[i % len(cols)]
        with col:
            if st.button(f"{i+1}", key=f"thumb_{i}", use_container_width=True):
                st.session_state.slide_idx = i
                st.session_state.manual_jump_num = i + 1  # Only update this, not the widget directly
                st.session_state.last_idx_for_jump = i
            col.image(slides[i], width=thumb_width)

# === After rendering widgets, update jump_num safely based on shadow variable ===
if st.session_state.jump_num != st.session_state.manual_jump_num:
    st.session_state.jump_num = st.session_state.manual_jump_num


