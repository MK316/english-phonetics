import streamlit as st
import requests
import re

st.set_page_config(page_title="Lecture Slides — Ch1", layout="wide")
st.title("📚 Lecture Slide Player — Chapter 1")

# --- Your GitHub folder (public) ---
GITHUB_OWNER  = "MK316"
GITHUB_REPO   = "english-phonetics"
GITHUB_BRANCH = "main"
FOLDER_PATH   = "pages/lecture/Ch1"   # where your JPEGs live
VALID_EXTS    = (".png", ".jpg", ".jpeg", ".webp")

def natural_key(s: str):
    """Sort key that treats numbers naturally: 1,2,10 (not 1,10,2)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

@st.cache_data(show_spinner=False, ttl=600)
def list_github_images(owner: str, repo: str, folder: str, branch: str):
    """
    Return naturally-sorted RAW URLs + filenames for images in a GitHub folder.
    """
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

try:
    slides, filenames = list_github_images(GITHUB_OWNER, GITHUB_REPO, FOLDER_PATH, GITHUB_BRANCH)
except Exception as e:
    st.error(f"Failed to load images: {e}")
    st.stop()

if not slides:
    st.warning("No image files found in the folder.")
    st.stop()

# --- Session state ---
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0

def clamp(i: int) -> int:
    return max(0, min(len(slides) - 1, i))

# --- Controls ---
left, mid, right = st.columns([1, 2, 1])
with left:
    if st.button("⬅️ Previous", use_container_width=True):
        st.session_state.slide_idx = clamp(st.session_state.slide_idx - 1)
with right:
    if st.button("Next ➡️", use_container_width=True):
        st.session_state.slide_idx = clamp(st.session_state.slide_idx + 1)
with mid:
    cur = st.session_state.slide_idx + 1
    jump = st.number_input("Jump to slide", min_value=1, max_value=len(slides), value=cur, step=1)
    if jump != cur:
        st.session_state.slide_idx = int(jump) - 1

# --- Display ---
idx = st.session_state.slide_idx
st.markdown(
    f"**Slide {idx + 1} / {len(slides)}** — *{filenames[idx]}*  \n"
    f"<small><code>{slides[idx]}</code></small>",
    unsafe_allow_html=True,
)
st.image(slides[idx], use_container_width=True, caption=f"Slide {idx + 1}")

# Optional thumbnails (first 10)
with st.expander("Thumbnails"):
    cols = st.columns(min(10, len(slides)))
    for i, c in enumerate(cols):
        if i < len(slides):
            if c.button(f"{i+1}", key=f"thumb_{i}"):
                st.session_state.slide_idx = i
            c.image(slides[i], use_column_width=True)
