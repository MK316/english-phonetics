# ... [Keep your import section the same] ...
import re
import io
import math
import requests
from PIL import Image
import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="Lecture Slide Player - Chapter 2", layout="wide")
st.markdown("#### 📗 Chapter 3: English consonants and allophonic rules")


# ------------ CONFIG ------------
GITHUB_OWNER  = "MK316"
GITHUB_REPO   = "english-phonetics"
GITHUB_BRANCH = "main"
FOLDER_PATH   = "pages/lecture/Ch03"

FILENAME_PREFIX = "Ch3."
FILENAME_EXT    = ".png"
START_INDEX     = 1
END_INDEX       = 47

THUMBS_PER_PAGE = 12
THUMB_COLS      = 6
THUMB_MAX_W     = 160
TIMEOUT         = 8

RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{GITHUB_BRANCH}/{FOLDER_PATH}"

def natural_key(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]

def _get(url: str) -> bytes:
    r = requests.get(url, timeout=TIMEOUT)
    r.raise_for_status()
    return r.content

@st.cache_data(show_spinner=False, ttl=3600)
def discover_pngs_by_pattern(raw_base: str, prefix: str, ext: str, start_i: int, end_i: int):
    found = []
    for i in range(start_i, end_i + 1):
        name = f"{prefix}{i:03d}{ext}"
        url  = f"{raw_base}/{name}"
        try:
            r = requests.get(url, stream=True, timeout=TIMEOUT)
            exists = r.status_code == 200
            r.close()
        except Exception:
            exists = False
        if exists:
            found.append((name, url))
    found.sort(key=lambda x: natural_key(x[0]))
    return [u for _, u in found], [n for n, _ in found]

@st.cache_data(show_spinner=False, ttl=3600)
def get_thumb_bytes(url: str, max_w: int = THUMB_MAX_W) -> bytes:
    raw = _get(url)
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    w, h = im.size
    if w > max_w:
        new_h = int(h * (max_w / w))
        im = im.resize((max_w, new_h), Image.LANCZOS)
    if im.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    buf = io.BytesIO()
    im.save(buf, format="WEBP", quality=80, method=6)
    return buf.getvalue()

# ---------- Discover slides ----------
slides, filenames = discover_pngs_by_pattern(
    RAW_BASE, FILENAME_PREFIX, FILENAME_EXT, START_INDEX, END_INDEX
)

if not slides:
    st.error("⚠️ No PNG files found.")
    st.stop()

# ---- Session state init ----
st.session_state.setdefault("slide_idx", 0)
st.session_state.setdefault("thumb_page", 1)
st.session_state.setdefault("fit_to_height", True)
st.session_state.setdefault("vh_percent", 88)
st.session_state.setdefault("display_width_px", 1000)
st.session_state.setdefault("thumbs_cache", {})

# --- Navigation callbacks ---
def go_prev():
    st.session_state.slide_idx = (st.session_state.slide_idx - 1) % len(slides)

def go_next():
    st.session_state.slide_idx = (st.session_state.slide_idx + 1) % len(slides)

def go_to_slide():
    num = st.session_state.slide_input
    if 1 <= num <= len(slides):
        st.session_state.slide_idx = num - 1

# ===== Sidebar =====
with st.sidebar:
    st.subheader("Controls")
    nav = st.columns([1, 1, 2])
    with nav[0]:
        st.button("◀️", use_container_width=True, on_click=go_prev)
    with nav[1]:
        st.button("▶️", use_container_width=True, on_click=go_next)
    with nav[2]:
        st.markdown(
            f"<div style='text-align:right; font-weight:600;'>{st.session_state.slide_idx + 1} / {len(slides)}</div>",
            unsafe_allow_html=True
        )

    st.toggle("Fit main slide to screen height", key="fit_to_height")
    if st.session_state.fit_to_height:
        st.slider("Height % of screen", 60, 95, key="vh_percent")
    else:
        st.slider("Slide width (px)", 700, 1400, key="display_width_px")

    st.number_input(
        "Go to Slide #",
        min_value=1,
        max_value=len(slides),
        step=1,
        key="slide_input",
        on_change=go_to_slide
    )

# ===== Main Slide =====
idx = st.session_state.slide_idx
if st.session_state.fit_to_height:
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center;">
            <img
                src="{slides[idx]}"
                alt="Slide {idx + 1}"
                style="
                    max-height: {st.session_state.vh_percent}vh;
                    width: auto;
                    height: auto;
                    object-fit: contain;
                    border: 1px solid #ccc;
                    box-shadow: 2px 2px 6px rgba(0,0,0,0.1);
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
        caption=f"Slide {idx + 1} / {len(slides)}",
        width=st.session_state.display_width_px,
        use_container_width=False
    )


# ===== Thumbnails =====
with st.expander("📑 Thumbnails", expanded=False):
    total = len(slides)
    pages = max(1, math.ceil(total / THUMBS_PER_PAGE))

    cols_top = st.columns(3)
    with cols_top[0]:
        st.caption(f"Total slides: {total}")
    with cols_top[1]:
        st.number_input("Thumbnail page", min_value=1, max_value=pages, step=1, key="thumb_page")
    with cols_top[2]:
        st.caption(f"Page size: {THUMBS_PER_PAGE}")

    start = (st.session_state.thumb_page - 1) * THUMBS_PER_PAGE
    end = min(start + THUMBS_PER_PAGE, total)
    page_urls = slides[start:end]

    cols = st.columns(min(THUMB_COLS, THUMBS_PER_PAGE))
    for local_i, url in enumerate(page_urls):
        global_idx = start + local_i
        col = cols[local_i % len(cols)]
        with col:
            if url not in st.session_state.thumbs_cache:
                st.session_state.thumbs_cache[url] = get_thumb_bytes(url)
            thumb_bytes = st.session_state.thumbs_cache[url]
            if st.button(f"{global_idx + 1}", key=f"thumb_btn_{global_idx}", use_container_width=True):
                st.session_state.slide_idx = global_idx
            st.image(thumb_bytes, width=150)
