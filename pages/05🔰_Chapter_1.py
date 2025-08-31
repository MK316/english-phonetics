import re
import io
import math
import requests
from PIL import Image
import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="Lecture Slide Player - Chapter 1", layout="wide")
st.markdown("#### 📗 Chapter 1: Articulation and Acoustics")

# ------------ CONFIG (edit as needed) ------------
GITHUB_OWNER  = "MK316"
GITHUB_REPO   = "english-phonetics"
GITHUB_BRANCH = "main"
FOLDER_PATH   = "pages/lecture/Ch01"   # path inside the repo

# Confirmed filenames like: F25_Ch01.001.png, F25_Ch01.002.png ...
FILENAME_PREFIX = "F25_Ch01."
FILENAME_EXT    = ".png"
START_INDEX     = 1
END_INDEX       = 120   # adjust to your max slide number

# UI / perf
THUMBS_PER_PAGE = 12     # how many thumbs to render at once
THUMB_COLS      = 6      # columns in thumb grid
THUMB_MAX_W     = 160    # pixel width of each thumb (small = faster)
TIMEOUT         = 8      # seconds for HTTP requests
# --------------------------------------------------

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{FOLDER_PATH}"

def natural_key(s: str):
    """Sort like humans (e.g., 2 before 10)."""
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def _get(url: str) -> bytes:
    """Download bytes; simple GET with timeout."""
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.content

@st.cache_data(show_spinner=False, ttl=3600)
def discover_pngs_by_pattern(raw_base: str, prefix: str, ext: str, start_i: int, end_i: int):
    """Probe sequentially named PNGs like F25_Ch01.001.png ... (no GitHub API)."""
    found = []
    for i in range(start_i, end_i + 1):
        name = f"{prefix}{i:03d}{ext}"
        url  = f"{raw_base}/{name}"
        # HEAD can be slower on some CDNs; do a quick GET of first bytes by streaming
        try:
            r = requests.get(url, stream=True, timeout=TIMEOUT)
            exists = r.status_code == 200
            r.close()
        except Exception:
            exists = False
        if exists:
            found.append((name, url))
    found.sort(key=lambda x: natural_key(x[0]))
    names = [n for n, _ in found]
    urls  = [u for _, u in found]
    return urls, names

@st.cache_data(show_spinner=False, ttl=3600)
def get_thumb_bytes(url: str, max_w: int = THUMB_MAX_W) -> bytes:
    """
    Download an image once, generate a tiny thumbnail, and cache the bytes (WEBP).
    Huge speedup for grids because clients receive small images.
    """
    raw = _get(url)
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    w, h = im.size
    if w > max_w:
        new_h = int(h * (max_w / w))
        im = im.resize((max_w, new_h), Image.LANCZOS)

    # Convert RGBA -> RGB to avoid WEBP alpha bloat if possible
    if im.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")

    buf = io.BytesIO()
    # WEBP ~ small size, good quality
    im.save(buf, format="WEBP", quality=80, method=6)
    return buf.getvalue()

# ---------- Discover slides ----------
slides, filenames = discover_pngs_by_pattern(
    RAW_BASE, FILENAME_PREFIX, FILENAME_EXT, START_INDEX, END_INDEX
)

if not slides:
    st.error(
        "⚠️ No PNG files found with the pattern F25_Ch01.001.png ... "
        "Check folder path, file names, and END_INDEX."
    )
    st.stop()

# ---- Session state ----
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0
if "jump_num" not in st.session_state:
    st.session_state.jump_num = st.session_state.slide_idx + 1
if "pending_jump" not in st.session_state:
    st.session_state.pending_jump = False
if "thumb_page" not in st.session_state:
    st.session_state.thumb_page = 1  # pagination for thumbs

def clamp(i: int) -> int:
    return max(0, min(len(slides) - 1, i))

# If a thumbnail was clicked previously, sync jump_num BEFORE widgets render
if st.session_state.pending_jump:
    st.session_state.jump_num = st.session_state.slide_idx + 1
    st.session_state.pending_jump = False

def on_jump_change():
    st.session_state.slide_idx = clamp(int(st.session_state.jump_num) - 1)

# ===== Sidebar controls =====
with st.sidebar:
    st.subheader("Controls")
    st.number_input(
        "Jump to slide",
        min_value=1,
        max_value=len(slides),
        step=1,
        key="jump_num",
        on_change=on_jump_change,
    )
    fit_to_width = st.toggle("Fit image to available width", value=True)
    if not fit_to_width:
        display_width = st.slider("Slide width (px)", 700, 1400, 1000, step=50)

# ===== Main slide =====
idx = st.session_state.slide_idx
if fit_to_width:
    st.image(slides[idx], use_column_width=True, caption=f"Slide {idx + 1} / {len(slides)}")
else:
    st.image(slides[idx], width=display_width, caption=f"Slide {idx + 1} / {len(slides)}")

# ===== Thumbnails (paginated + optimized) =====
with st.expander("Thumbnails"):
    total = len(slides)
    pages = max(1, math.ceil(total / THUMBS_PER_PAGE))

    cols_top = st.columns(3)
    with cols_top[0]:
        st.caption(f"Total slides: {total}")
    with cols_top[1]:
        st.number_input(
            "Thumbnail page",
            min_value=1,
            max_value=pages,
            step=1,
            key="thumb_page"
        )
    with cols_top[2]:
        st.caption(f"Page size: {THUMBS_PER_PAGE}")

    start = (st.session_state.thumb_page - 1) * THUMBS_PER_PAGE
    end   = min(start + THUMBS_PER_PAGE, total)
    page_urls = slides[start:end]

    cols = st.columns(min(THUMB_COLS, THUMBS_PER_PAGE))
    for local_i, url in enumerate(page_urls):
        global_idx = start + local_i
        col = cols[local_i % len(cols)]
        with col:
            # tiny, cached, recompressed thumbnail
            thumb_bytes = get_thumb_bytes(url)
            if st.button(f"{global_idx + 1}", key=f"thumb_btn_{global_idx}", use_container_width=True):
                st.session_state.slide_idx = global_idx
                st.session_state.pending_jump = True
            st.image(thumb_bytes, use_container_width=True)

#---------- Previous code (working)

# import re
# import requests
# import streamlit as st

# # ---------------- Page setup ----------------
# st.set_page_config(page_title="Lecture Slide Player - Chapter 1", layout="wide")
# st.markdown("#### 📗 Chapter 1: Articulation and Acoustics")

# # ------------ CONFIG (edit as needed) ------------
# GITHUB_OWNER  = "MK316"
# GITHUB_REPO   = "english-phonetics"
# GITHUB_BRANCH = "main"
# FOLDER_PATH   = "pages/lecture/Ch01"   # path inside the repo

# # Confirmed filenames like: F25_Ch01.001.png, F25_Ch01.002.png, ...
# FILENAME_PREFIX = "F25_Ch01."
# FILENAME_EXT    = ".png"
# START_INDEX     = 1
# END_INDEX       = 300          # upper bound to probe; set to your max (e.g., 120)

# DISPLAY_WIDTH_DEFAULT = 900
# THUMB_MAX, THUMB_COLS = 40, 10
# TIMEOUT = 8  # seconds for HTTP checks
# # --------------------------------------------------

# RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{FOLDER_PATH}"

# def natural_key(s: str):
#     # human sort: slide2 before slide10
#     return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

# def _exists(url: str) -> bool:
#     try:
#         r = requests.head(url, timeout=TIMEOUT)
#         if r.status_code == 405:  # if HEAD blocked, try lightweight GET
#             r = requests.get(url, stream=True, timeout=TIMEOUT)
#         return r.status_code == 200
#     except Exception:
#         return False

# @st.cache_data(show_spinner=False, ttl=600)
# def discover_pngs_by_pattern(raw_base: str, prefix: str, ext: str, start_i: int, end_i: int):
#     """Probe F25_Ch01.{i:03d}.png under the raw GitHub folder (no GitHub API)."""
#     found = []
#     for i in range(start_i, end_i + 1):
#         name = f"{prefix}{i:03d}{ext}"   # e.g., F25_Ch01.001.png
#         url  = f"{raw_base}/{name}"
#         if _exists(url):
#             found.append((name, url))

#     found.sort(key=lambda x: natural_key(x[0]))
#     names = [n for n, _ in found]
#     urls  = [u for _, u in found]
#     return urls, names

# # ---------- Discover slides ----------
# slides, filenames = discover_pngs_by_pattern(
#     RAW_BASE, FILENAME_PREFIX, FILENAME_EXT, START_INDEX, END_INDEX
# )

# if not slides:
#     st.error(
#         "No PNG files discovered with the pattern F25_Ch01.{i:03d}.png.\n"
#         "• Verify the folder path and filename pattern.\n"
#         "• If your files stop at a smaller number (e.g., 088), set END_INDEX accordingly."
#     )
#     st.stop()

# # ---- Session state init ----
# if "slide_idx" not in st.session_state:
#     st.session_state.slide_idx = 0
# if "jump_num" not in st.session_state:
#     st.session_state.jump_num = st.session_state.slide_idx + 1
# if "pending_jump" not in st.session_state:
#     st.session_state.pending_jump = False  # set True after thumbnail click

# def clamp(i: int) -> int:
#     return max(0, min(len(slides) - 1, i))

# # --- IMPORTANT: if a thumbnail was clicked in the previous run,
# # sync the number_input value BEFORE rendering the widget this run.
# if st.session_state.pending_jump:
#     st.session_state.jump_num = st.session_state.slide_idx + 1
#     st.session_state.pending_jump = False  # consumed

# def on_jump_change():
#     st.session_state.slide_idx = clamp(int(st.session_state.jump_num) - 1)

# # ===== Sidebar controls =====
# with st.sidebar:
#     st.subheader("Controls")
#     # Do not pass value= when using key; avoids overwriting state
#     st.number_input(
#         "Jump to slide",
#         min_value=1,
#         max_value=len(slides),
#         step=1,
#         key="jump_num",
#         on_change=on_jump_change,
#     )
#     display_width = st.slider("Slide width (px)", 700, 1100, DISPLAY_WIDTH_DEFAULT, step=50)

# # ===== Main area: slide + caption =====
# idx = st.session_state.slide_idx
# st.image(slides[idx], width=display_width, caption=f"Slide {idx + 1} / {len(slides)}")

# # ===== Thumbnails =====
# with st.expander("Thumbnails"):
#     n = min(THUMB_MAX, len(slides))
#     cols = st.columns(THUMB_COLS if n >= THUMB_COLS else n)
#     thumb_width = int(display_width / THUMB_COLS) if THUMB_COLS else 120

#     for i in range(n):
#         col = cols[i % len(cols)]
#         with col:
#             if st.button(f"{i+1}", key=f"thumb_{i}", use_container_width=True):
#                 # Update the source-of-truth index
#                 st.session_state.slide_idx = i
#                 # Request that the jump widget be updated on the next run (before render)
#                 st.session_state.pending_jump = True
#             col.image(slides[i], width=thumb_width)
