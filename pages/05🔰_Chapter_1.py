import re
import requests
import streamlit as st

st.set_page_config(page_title="Lecture Slide Player — Chapter 1", layout="wide")
st.header("📚 Chapter 1: Articulation and acoustics")

# ------------ CONFIG ------------
GITHUB_OWNER  = "MK316"
GITHUB_REPO   = "english-phonetics"
GITHUB_BRANCH = "main"
FOLDER_PATH   = "pages/lecture/Ch01"   # folder inside repo
VALID_EXTS    = (".png", ".jpg", ".jpeg", ".webp")
DISPLAY_WIDTH_DEFAULT = 900
THUMB_MAX, THUMB_COLS = 20, 10
# ---------------------------------

def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def _auth_headers():
    token = st.secrets.get("GITHUB_TOKEN", None)
    return {"Authorization": f"token {token}"} if token else {}

@st.cache_data(show_spinner=False, ttl=600)
def list_images(owner: str, repo: str, folder: str, branch: str):
    """
    Try contents API (with per_page=100). If that fails, fall back to git/trees API (recursive).
    Returns (urls, names) for files in `folder` with VALID_EXTS.
    """
    headers = _auth_headers()

    # -------- Try 1: contents API with pagination (cheap, simple) ----------
    files = []
    page = 1
    while True:
        api = (
            f"https://api.github.com/repos/{owner}/{repo}/contents/{folder}"
            f"?ref={branch}&per_page=100&page={page}"
        )
        r = requests.get(api, headers=headers, timeout=20)
        if r.status_code == 200:
            batch = r.json()
            # If GitHub returns a dict (not list), treat as error/fallback
            if isinstance(batch, dict):
                break
            if not batch:
                break
            files.extend(batch)
            # If less than per_page, we are done
            if len(batch) < 100:
                break
            page += 1
        else:
            # contents API failed -> use trees API
            files = None
            break

    urls, names = [], []
    if files:
        valid = [
            it for it in files
            if it.get("type") == "file"
            and it.get("name", "").lower().endswith(VALID_EXTS)
        ]
        valid.sort(key=lambda x: natural_key(x["name"]))
        raw_base = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{folder}"
        urls  = [f"{raw_base}/{f['name']}" for f in valid]
        names = [f["name"] for f in valid]
        if urls:
            return urls, names

    # -------- Try 2: git/trees API (recursive list of the whole repo) ----------
    tree_api = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    r = requests.get(tree_api, headers=headers, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(
            f"GitHub API error {r.status_code} while listing files.\n"
            f"Tip: Add GITHUB_TOKEN to Streamlit secrets to avoid rate limits."
        )

    data = r.json()
    tree = data.get("tree", [])
    # Filter paths inside our folder with valid extensions
    prefix = folder.rstrip("/") + "/"
    hits = [
        it["path"] for it in tree
        if it.get("type") == "blob"
        and it.get("path", "").startswith(prefix)
        and it.get("path", "").lower().endswith(VALID_EXTS)
    ]
    # Keep only the filename component for display, but build raw URLs with full path
    hits.sort(key=lambda p: natural_key(p.rsplit("/", 1)[-1]))
    urls = [f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{p}" for p in hits]
    names = [p.rsplit("/", 1)[-1] for p in hits]
    if not urls:
        raise RuntimeError(
            "No image files found. "
            "Check folder/branch names and file extensions."
        )
    return urls, names

# ---------- Load slide list ----------
slides, filenames = list_images(GITHUB_OWNER, GITHUB_REPO, FOLDER_PATH, GITHUB_BRANCH)
if not slides:
    st.warning("No image files found in the folder.")
    st.stop()

# ---- Session state init ----
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0
if "jump_num" not in st.session_state:
    # Initialize jump widget value BEFORE rendering the widget
    st.session_state.jump_num = st.session_state.slide_idx + 1

def clamp(i: int) -> int:
    return max(0, min(len(slides) - 1, i))

def on_jump_change():
    st.session_state.slide_idx = clamp(int(st.session_state.jump_num) - 1)

# ===== Sidebar controls =====
with st.sidebar:
    st.subheader("Controls")
    # IMPORTANT: no 'value=' here; we let the key drive the widget value.
    st.number_input(
        "Jump to slide",
        min_value=1,
        max_value=len(slides),
        step=1,
        key="jump_num",
        on_change=on_jump_change,
    )
    display_width = st.slider("Slide width (px)", 700, 1100, DISPLAY_WIDTH_DEFAULT, step=50)

# Keep widget in sync if slide_idx changed elsewhere (e.g., via thumbnails)
if st.session_state.jump_num != st.session_state.slide_idx + 1:
    st.session_state.jump_num = st.session_state.slide_idx + 1

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
                st.session_state.slide_idx = i  # one-click update
            col.image(slides[i], width=thumb_width)
