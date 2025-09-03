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
        # Quick existence check
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
    im.save(buf, format="WEBP", quality=80, method=6)  # WEBP small & crisp
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

# ---- Session state init ----
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0
if "thumb_page" not in st.session_state:
    st.session_state.thumb_page = 1
if "fit_to_height" not in st.session_state:
    st.session_state.fit_to_height = True
if "vh_percent" not in st.session_state:
    st.session_state.vh_percent = 88
if "display_width_px" not in st.session_state:
    st.session_state.display_width_px = 1000

def clamp_index(i: int, n: int) -> int:
    """Clamp index i into [0, n-1]."""
    if n <= 0:
        return 0
    return max(0, min(n - 1, i))

# --- Navigation callbacks (one click, wrap-around) ---
def go_prev():
    st.session_state.slide_idx = (st.session_state.slide_idx - 1) % len(slides)

def go_next():
    st.session_state.slide_idx = (st.session_state.slide_idx + 1) % len(slides)

# ===== Sidebar controls =====
with st.sidebar:
    st.subheader("Controls")

    # Simple NEXT / PREV buttons (place BEFORE reading idx)
    nav = st.columns([1, 1, 2])
    with nav[0]:
        st.button("◀️ Prev", key="btn_prev", use_container_width=True, on_click=go_prev)
    with nav[1]:
        st.button("Next ▶️", key="btn_next", use_container_width=True, on_click=go_next)
    with nav[2]:
        # live display of current position
        st.markdown(
            f"<div style='text-align:right; font-weight:600;'>"
            f"{st.session_state.slide_idx + 1} / {len(slides)}</div>",
            unsafe_allow_html=True
        )

    # View options (state-backed widgets)
    st.toggle("Fit main slide to screen height", key="fit_to_height")
    if st.session_state.fit_to_height:
        st.slider("Height % of screen", 60, 95, key="vh_percent")
    else:
        st.slider("Slide width (px)", 700, 1400, key="display_width_px")

# ===== Main slide =====
idx = st.session_state.slide_idx

if st.session_state.fit_to_height:
    st.markdown(
        f"""
        <div style="display:flex;justify-content:center;">
          <img
            src="{slides[idx]}"
            alt="Slide {idx + 1}"
            style="
              max-width: 100%;
              max-height: {st.session_state.vh_percent}vh;
              width: auto;
              height: auto;
              object-fit: contain;
              display: block;
            "
          />
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(f"Slide {idx + 1} / {len(slides)}")
else:
    st.image(
        slides[idx],
        width=st.session_state.display_width_px,
        caption=f"Slide {idx + 1} / {len(slides)}"
    )

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
    col_count = len(cols)
    for local_i, url in enumerate(page_urls):
        global_idx = start + local_i
        col = cols[local_i % col_count]
        with col:
            thumb_bytes = get_thumb_bytes(url)
            if st.button(f"{global_idx + 1}", key=f"thumb_btn_{global_idx}", use_container_width=True):
                st.session_state.slide_idx = global_idx
            st.image(thumb_bytes, width=150)


# import re
# import io
# import math
# import requests
# from PIL import Image
# import streamlit as st

# # ---------------- Page setup ----------------
# st.set_page_config(page_title="Lecture Slide Player - Chapter 1", layout="wide")
# st.markdown("#### 📗 Chapter 1: Articulation and Acoustics")

# # ------------ CONFIG (edit as needed) ------------
# GITHUB_OWNER  = "MK316"
# GITHUB_REPO   = "english-phonetics"
# GITHUB_BRANCH = "main"
# FOLDER_PATH   = "pages/lecture/Ch01"   # path inside the repo

# # Confirmed filenames like: F25_Ch01.001.png, F25_Ch01.002.png ...
# FILENAME_PREFIX = "F25_Ch01."
# FILENAME_EXT    = ".png"
# START_INDEX     = 1
# END_INDEX       = 120   # adjust to your max slide number

# # UI / perf
# THUMBS_PER_PAGE = 12     # how many thumbs to render at once
# THUMB_COLS      = 6      # columns in thumb grid
# THUMB_MAX_W     = 160    # pixel width of each thumb (small = faster)
# TIMEOUT         = 8      # seconds for HTTP requests
# # --------------------------------------------------

# RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{FOLDER_PATH}"

# def natural_key(s: str):
#     """Sort like humans (e.g., 2 before 10)."""
#     return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

# def _get(url: str) -> bytes:
#     """Download bytes; simple GET with timeout."""
#     r = requests.get(url, timeout=TIMEOUT)
#     r.raise_for_status()
#     return r.content

# @st.cache_data(show_spinner=False, ttl=3600)
# def discover_pngs_by_pattern(raw_base: str, prefix: str, ext: str, start_i: int, end_i: int):
#     """Probe sequentially named PNGs like F25_Ch01.001.png ... (no GitHub API)."""
#     found = []
#     for i in range(start_i, end_i + 1):
#         name = f"{prefix}{i:03d}{ext}"
#         url  = f"{raw_base}/{name}"
#         # Quick existence check
#         try:
#             r = requests.get(url, stream=True, timeout=TIMEOUT)
#             exists = r.status_code == 200
#             r.close()
#         except Exception:
#             exists = False
#         if exists:
#             found.append((name, url))
#     found.sort(key=lambda x: natural_key(x[0]))
#     names = [n for n, _ in found]
#     urls  = [u for _, u in found]
#     return urls, names

# @st.cache_data(show_spinner=False, ttl=3600)
# def get_thumb_bytes(url: str, max_w: int = THUMB_MAX_W) -> bytes:
#     """
#     Download an image once, generate a tiny thumbnail, and cache the bytes (WEBP).
#     Huge speedup for grids because clients receive small images.
#     """
#     raw = _get(url)
#     im = Image.open(io.BytesIO(raw)).convert("RGBA")
#     w, h = im.size
#     if w > max_w:
#         new_h = int(h * (max_w / w))
#         im = im.resize((max_w, new_h), Image.LANCZOS)

#     # Convert RGBA -> RGB to avoid WEBP alpha bloat if possible
#     if im.mode in ("RGBA", "LA"):
#         bg = Image.new("RGB", im.size, (255, 255, 255))
#         bg.paste(im, mask=im.split()[-1])
#         im = bg
#     else:
#         im = im.convert("RGB")

#     buf = io.BytesIO()
#     # WEBP ~ small size, good quality
#     im.save(buf, format="WEBP", quality=80, method=6)
#     return buf.getvalue()

# # ---------- Discover slides ----------
# slides, filenames = discover_pngs_by_pattern(
#     RAW_BASE, FILENAME_PREFIX, FILENAME_EXT, START_INDEX, END_INDEX
# )

# if not slides:
#     st.error(
#         "⚠️ No PNG files found with the pattern F25_Ch01.001.png ... "
#         "Check folder path, file names, and END_INDEX."
#     )
#     st.stop()

# # ---- Session state init ----
# if "slide_idx" not in st.session_state:
#     st.session_state.slide_idx = 0
# if "thumb_page" not in st.session_state:
#     st.session_state.thumb_page = 1
# if "fit_to_height" not in st.session_state:
#     st.session_state.fit_to_height = True
# if "vh_percent" not in st.session_state:
#     st.session_state.vh_percent = 88
# if "display_width_px" not in st.session_state:
#     st.session_state.display_width_px = 1000

# def clamp_index(i: int, n: int) -> int:
#     """Clamp index i into [0, n-1]."""
#     if n <= 0:
#         return 0
#     return max(0, min(n - 1, i))

# # ===== Sidebar controls =====
# with st.sidebar:
#     st.subheader("Controls")

#     # Not bound to Session State; we read the returned value
#     jump_val = st.number_input(
#         "Jump to slide",
#         min_value=1,
#         max_value=len(slides),
#         step=1,
#         value=st.session_state.slide_idx + 1,  # initial display only
#     )
#     # If user changed, update slide_idx (no on_change, no key → no conflicts)
#     new_idx = clamp_index(jump_val - 1, len(slides))
#     if new_idx != st.session_state.slide_idx:
#         st.session_state.slide_idx = new_idx

#     # View options (state-backed widgets; no default 'value=' passed)
#     st.toggle("Fit main slide to screen height", key="fit_to_height")
#     if st.session_state.fit_to_height:
#         st.slider("Height % of screen", 60, 95, key="vh_percent")
#     else:
#         st.slider("Slide width (px)", 700, 1400, key="display_width_px")

# # ===== Main slide =====
# idx = st.session_state.slide_idx

# if st.session_state.fit_to_height:
#     # Fit to viewport height; width scales automatically, preserving aspect ratio
#     st.markdown(
#         f"""
#         <div style="display:flex;justify-content:center;">
#           <img
#             src="{slides[idx]}"
#             alt="Slide {idx + 1}"
#             style="
#               max-width: 100%;
#               max-height: {st.session_state.vh_percent}vh;
#               width: auto;
#               height: auto;
#               object-fit: contain;
#               display: block;
#             "
#           />
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )
#     st.caption(f"Slide {idx + 1} / {len(slides)}")
# else:
#     st.image(
#         slides[idx],
#         width=st.session_state.display_width_px,
#         caption=f"Slide {idx + 1} / {len(slides)}"
#     )

# # ===== Thumbnails (paginated + optimized) =====
# with st.expander("Thumbnails"):
#     total = len(slides)
#     pages = max(1, math.ceil(total / THUMBS_PER_PAGE))

#     cols_top = st.columns(3)
#     with cols_top[0]:
#         st.caption(f"Total slides: {total}")
#     with cols_top[1]:
#         st.number_input(
#             "Thumbnail page",
#             min_value=1,
#             max_value=pages,
#             step=1,
#             key="thumb_page"
#         )
#     with cols_top[2]:
#         st.caption(f"Page size: {THUMBS_PER_PAGE}")

#     start = (st.session_state.thumb_page - 1) * THUMBS_PER_PAGE
#     end   = min(start + THUMBS_PER_PAGE, total)
#     page_urls = slides[start:end]

#     cols = st.columns(min(THUMB_COLS, THUMBS_PER_PAGE))
#     col_count = len(cols)
#     for local_i, url in enumerate(page_urls):
#         global_idx = start + local_i
#         col = cols[local_i % col_count]
#         with col:
#             # tiny, cached, recompressed thumbnail (fixed width => sharper)
#             thumb_bytes = get_thumb_bytes(url)
#             if st.button(f"{global_idx + 1}", key=f"thumb_btn_{global_idx}", use_container_width=True):
#                 st.session_state.slide_idx = global_idx
#             st.image(thumb_bytes, width=150)
