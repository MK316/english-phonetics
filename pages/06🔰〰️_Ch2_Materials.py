import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Chapter 2 material", page_icon="📚", layout="wide")
st.title("📚 Ch.2 Materials")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Slide supplementary", "Videos", "Web links"])

# ---------------- Tab 1 ----------------

with tab1:
    st.markdown("#### Materials on slides")

    # (Optional) make expanders look like plain lines
    st.markdown(
        """
        <style>
          div[data-testid="stExpander"] { border: 0; background: transparent; }
          details > summary { font-weight: 600; font-size: 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Helper to accept either GitHub blob or RAW links
    def to_raw(url: str) -> str:
        if "raw.githubusercontent.com" in url or url.endswith("?raw=1"):
            return url
        return url.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")

    # Your media
    AUDIO_URL1 = "https://github.com/MK316/english-phonetics/blob/main/pages/audio/Ch2-Slide6.mp3"
    AUDIO_URL2 = "https://github.com/MK316/english-phonetics/blob/main/pages/audio/Ch2-Slide11a.mp3"
    AUDIO_URL3 = "https://github.com/MK316/english-phonetics/blob/main/pages/audio/Ch2-Slide11b.mp3"
    AUDIO_URL4 = "https://github.com/MK316/english-phonetics/blob/main/pages/audio/Ch2-Slide12.mp3"
    
    # Use an MP4 / WebM file or a YouTube link for video:
    VIDEO_URL = "https://youtu.be/dQw4w9WgXcQ"  # <-- replace with your real link (or raw GitHub MP4)

    # Foldable line 1 — text + audio
    with st.expander("Slide #6 - Same sound?", expanded=False):
        st.markdown("Words you've heard all include the same sound?")
        st.audio(to_raw(AUDIO_URL1), format="audio/mp3")

    # Foldable line 1 — text + audio
    with st.expander("Slide #11 - 'Mary-merry-marry", expanded=False):
        st.markdown("Neutralization: 'Mary-merry-marry")
        st.audio(to_raw(AUDIO_URL2), format="audio/mp3")
        st.audio(to_raw(AUDIO_URL3), format="audio/mp3")

    with st.expander("Slide #14 - writer vs. rider", expanded=False):
        st.markdown("Listen to the vowels to hear the variation between 'writer' and 'rider'.")
        st.audio(to_raw(AUDIO_URL4), format="audio/mp3")
    
    
    # Foldable line 2 — video
    with st.expander("Slide #8", expanded=False):
        st.markdown("Demonstration clip (articulation walkthrough).")
        st.video(VIDEO_URL)


# ---------------- Tab 2 ----------------
with tab2:
    st.subheader("Schedule (Example Table)")


# ---------------- Tab 3 ----------------
with tab3:
    st.markdown("- [Sample PDF](https://example.com/sample.pdf)")

