import streamlit as st

# === SETTINGS ===
TOTAL_SLIDES = 88
SLIDE_PREFIX = "slide"
SLIDE_EXT = ".png"
DISPLAY_WIDTH_DEFAULT = 900
THUMB_MAX, THUMB_COLS = 20, 10

RAW_URL_BASE = "https://raw.githubusercontent.com/MK316/english-phonetics/main/pages/lecture/Ch01"

# === PAGE SETUP ===
st.set_page_config(page_title="Lecture Slide Player — Chapter 1", layout="wide")
st.header("📚 Chapter 1: Articulation and acoustics")

# === SLIDE URL BUILDER ===
def build_slide_urls():
    urls = []
    names = []
    for i in range(1, TOTAL_SLIDES + 1):
        name = f"{SLIDE_PREFIX}{i:02d}{SLIDE_EXT}"
        url = f"{RAW_URL_BASE}/{name}"
        urls.append(url)
        names.append(name)
    return urls, names

slides, filenames = build_slide_urls()

# === SESSION STATE INIT ===
if "slide_idx" not in st.session_state:
    st.session_state.slide_idx = 0

def clamp(i: int) -> int:
    return max(0, min(len(slides) - 1, i))

def sync_from_jump():
    st.session_state.slide_idx = clamp(int(st.session_state.jump_num) - 1)

# === SIDEBAR ===
with st.sidebar:
    st.subheader("Controls")
    st.number_input(
        "Jump to slide",
        min_value=1,
        max_value=len(slides),
        step=1,
        key="jump_num",
        on_change=sync_from_jump,
    )
    display_width = st.slider("Slide width (px)", 700, 1100, DISPLAY_WIDTH_DEFAULT, step=50)

# === KEEP SLIDE-JUMP SYNCED ===
if "jump_num" not in st.session_state or st.session_state.jump_num != st.session_state.slide_idx + 1:
    st.session_state.jump_num = st.session_state.slide_idx + 1

# === MAIN SLIDE ===
idx = st.session_state.slide_idx
st.image(slides[idx], width=display_width, caption=f"Slide {idx + 1} / {len(slides)}")

# === THUMBNAILS ===
with st.expander("Thumbnails"):
    n = min(THUMB_MAX, len(slides))
    cols = st.columns(THUMB_COLS if n >= THUMB_COLS else n)
    thumb_width = int(display_width / THUMB_COLS) if THUMB_COLS else 120

    for i in range(n):
        col = cols[i % len(cols)]
        with col:
            if st.button(f"{i+1}", key=f"thumb_{i}", use_container_width=True):
                st.session_state.slide_idx = i
            col.image(slides[i], width=thumb_width)
