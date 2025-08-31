import re
import requests
import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="Lecture Slide Player - Chapter 1", layout="wide")
st.header("Chapter 1: Articulation and Acoustics")

# ------------ CONFIG ------------
GITHUB_OWNER  = "MK316"
GITHUB_REPO   = "english-phonetics"
GITHUB_BRANCH = "main"
FOLDER_PATH   = "pages/lecture/Ch01"   # case-sensitive path inside repo
VALID_EXTS    = (".png", ".jpg", ".jpeg", ".webp")
DISPLAY_WIDTH_DEFAULT = 900
THUMB_MAX, THUMB_COLS = 20, 10
# ---------------------------------

def natural_key(s: str):
    # Sort like humans (slide2 before slide10)
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def _auth_headers():
    # Optional: add GITHUB_TOKEN in Streamlit Secrets to avoid rate limits
    # Settings -> Secrets: GITHUB_TOKEN = "ghp_xxx..."
    token = st.secrets.get("GITHUB_TOKEN", None)
    return {"Authorization": f"token {token}"} if token else {}

def _raw_url(owner: str, repo: str, branch: str, path: str) -> str:
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}"

@st.cache_data(show_spinner=False, ttl=600)
def list_images_via_trees(owner: str, repo: str, folder: str, branch: str):
    """
    List all images under `folder` using GitHub git/trees API (recursive).
    Works even when the contents API is rate-limited or paginated.
    """
    headers = _auth_headers()
    tree_api = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    r = requests.get(tree_api, headers=headers, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"GitHub API error {r.status_code} while listing files.")

    data = r.json()
    tree = data.get("tree", [])

    # Build a case-sensitive prefix match (Git paths are case-sensitive)
    prefix = folder.strip("/") + "/"

    hits = []
    for it in tree:
        if it.get("type") != "blob":
            continue
        p = it.get("path", "")
        if not p.startswith(prefix):
            continue
        low = p.lower()
        if not low.endswith(VALID_EXTS):
            continue
        hits.append(p)

    # Sort by human order on the file's basename
    hits.sort(key=lambda p: natural_key(p.rsplit("/", 1)[-1]))

    urls  = [_raw_url(owner, repo, branch, p) for p in hits]
    names = [p.rsplit("/", 1)[-1] for p in hits]
    return urls, names, {"hits": len(hits), "sample": hits[:5]}

# ---------- Load slide list ----------
try:
    slides, filenames, dbg = list_images_via_trees(GITHUB_OWNER, GITHUB_REPO, FOLDER_PATH, GITHUB_BRANCH)
except Exception as e:
    st.error(f"Could not list images: {e}")
    st.info(
        "Tips:\n"
        "- Verify GITHUB_OWNER / GITHUB_REPO / GITHUB_BRANCH / FOLDER_PATH\n"
        "- Add GITHUB_TOKEN in Secrets to avoid rate limits\n"
        "- Ensure files end with .png/.jpg/.jpeg/.webp"
    )
    st.stop()

if not slides:
    st.warning("No image files found in the specified folder.")
    st.stop()

# Optional small debug panel (hide later)
with st.expander("Debug"):
    st.write(dbg)

# ---- Session state init ----
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0
if "jump_num" not in st.session_state:
    st.session_state.jump_num = st.session_state.slide_idx + 1

def clamp(i: int) -> int:
    return max(0, min(len(slides) - 1, i))

def on_jump_change():
    st.session_state.slide_idx = clamp(int(st.session_state.jump_num) - 1)

# ===== Sidebar controls =====
with st.sidebar:
    st.subheader("Controls")
    # IMPORTANT: do not pass `value=` when using key to avoid overwriting state
    st.number_input(
        "Jump to slide",
        min_value=1,
        max_value=len(slides),
        step=1,
        key="jump_num",
        on_change=on_jump_change,
    )
    display_width = st.slider("Slide width (px)", 700, 1100, DISPLAY_WIDTH_DEFAULT, step=50)

# Keep jump widget in sync if slide_idx changed via thumbnails
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
