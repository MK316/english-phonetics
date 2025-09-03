import streamlit as st
import io, requests, numpy as np
import matplotlib.pyplot as plt

# ---------- Page setup ----------
st.set_page_config(page_title="Multi-Apps", page_icon="🌀", layout="wide")
st.markdown("#### 🌀 Multi-Apps for Chapter 1")

# ---------- Tabs ----------
tab1, tab2, tab3 = st.tabs(["💦 Videos", "💦 Web links", "💦 Download"])

# =========================================================
# TAB 1 — Video links
# =========================================================
with tab1:
    st.subheader("🎬 Useful Videos")

    # Sample video list (replace URLs/titles with yours)
    videos = [
        {"title": "McGurk Effect (BBC)", "url": "https://www.youtube.com/embed/2k8fHR9jKVM?si=bQlOyoMNZEhnQ3Rf"},
        {"title": "How vocal folds work", "url": "https://www.youtube.com/embed/5QhVoaVUGmM?si=XNCbqRnVsG8oh8vS"},
        {"title": "How Does the Human Body Produce Voice and Speech?", "url": "https://www.youtube.com/embed/JF8rlKuSoFM?si=JSoICMOBWxrXdMn2"},
        {"title": "Vocal folds while singing", "url": "https://www.youtube.com/embed/-XGds2GAvGQ?si=a796eZI1vE87kiC3"}
    ]

    titles = [v["title"] for v in videos]
    choice = st.selectbox("Choose a video to play:", titles, key="tab1_video_choice")

    # Get selected video dict
    selected = next(v for v in videos if v["title"] == choice)

    # Control video size
    width = st.slider("Video width (px)", 400, 1000, 700, step=50)
    height = int(width * 9 / 16)  # keep 16:9 ratio

    st.markdown(
        f"""
        <div style="text-align: center;">
            <iframe width="{width}" height="{height}" 
                    src="{selected['url']}" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
            </iframe>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"[🔗 Open on YouTube]({selected['url']})")



# =========================================================
# TAB 2 — Web links
# =========================================================
with tab2:
    st.subheader("Web links")
    st.markdown("🐾 [Textbook online](https://linguistics.berkeley.edu/acip/): This is a resource site managed by the Department of Linguistics at UC Berkeley for the textbook A Course in Phonetics. It contains materials related to the illustrations and exercises presented in the book.")
    #st.markdown("🐾 [](): This video was provided by the National Institutes of Health.")
    #st.markdown("🐾 []()")
    #st.markdown("🐾 []()")

# =========================================================
# TAB 3 — Download files
# =========================================================
with tab3:
    st.subheader("File download")
    st.markdown("+ [IPA chart 2015](https://github.com/MK316/classmaterial/raw/main/Phone/IPA_Kiel_2015.pdf): IPA chart")
    st.caption("➡️ This IPA chart contains symbols that were agreed upon to represent the sounds of all the world’s languages. It is not a chart made specifically for English.")
    st.divider()

    # --------------------------
    # Audio players + waveform
    # --------------------------
    st.subheader("Audio practice")

    import io, requests, numpy as np
    import matplotlib.pyplot as plt

    # Convert normal GitHub URLs to RAW
    def to_raw(gh_url: str) -> str:
        if "raw.githubusercontent.com" in gh_url or gh_url.endswith("?raw=1"):
            return gh_url
        return gh_url.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")

    # Fetch bytes (cache to avoid re-downloading)
    @st.cache_data(show_spinner=False)
    def fetch_bytes(raw_url: str) -> bytes:
        r = requests.get(raw_url, timeout=20)
        r.raise_for_status()
        return r.content

    # Decode WAV to (y, sr). Tries soundfile → scipy → builtin wave (16/32-bit PCM).
    def load_wav_from_bytes(b: bytes):
        bio = io.BytesIO(b)

        # Try soundfile (most robust, handles many encodings)
        try:
            import soundfile as sf
            y, sr = sf.read(bio, always_2d=False)
            if y.ndim > 1:  # stereo → mono
                y = y.mean(axis=1)
            return y.astype(np.float32), int(sr)
        except Exception:
            pass

        # Try scipy
        try:
            from scipy.io import wavfile
            bio.seek(0)
            sr, y = wavfile.read(bio)
            if y.ndim > 1:
                y = y.mean(axis=1)
            # Normalize integer PCM to [-1, 1]
            if np.issubdtype(y.dtype, np.integer):
                maxv = np.iinfo(y.dtype).max
                y = y.astype(np.float32) / maxv
            else:
                y = y.astype(np.float32)
            return y, int(sr)
        except Exception:
            pass

        # Fallback: builtin wave (handles 8/16/32-bit)
        try:
            import wave, struct
            bio.seek(0)
            with wave.open(bio, "rb") as wf:
                n_channels = wf.getnchannels()
                sampwidth  = wf.getsampwidth()
                framerate  = wf.getframerate()
                n_frames   = wf.getnframes()
                frames = wf.readframes(n_frames)

            # Only handle 1, 2, or 4 byte widths here
            if sampwidth == 1:
                y = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
                y = (y - 128.0) / 128.0  # 8-bit unsigned
            elif sampwidth == 2:
                y = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            elif sampwidth == 4:
                y = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                return None, None  # 24-bit PCM etc. not handled here

            if n_channels > 1:
                y = y.reshape(-1, n_channels).mean(axis=1)
            return y, int(framerate)
        except Exception:
            return None, None

    # Plot waveform
    def plot_waveform(y: np.ndarray, sr: int, title: str):
        if y is None or sr is None:
            st.caption("Waveform preview unavailable for this file format.")
            return
        # Downsample for plotting (speed)
        max_points = 10000
        if y.size > max_points:
            idx = np.linspace(0, y.size - 1, max_points).astype(int)
            y_plot = y[idx]
            t = idx / sr
        else:
            y_plot = y
            t = np.arange(y.size) / sr

        fig, ax = plt.subplots(figsize=(8, 2.2))
        ax.plot(t, y_plot)
        ax.set_xlim(t[0], t[-1] if t.size else 1)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
        ax.set_title(title)
        ax.set_yticks([])
        ax.grid(True, alpha=0.2)
        st.pyplot(fig, clear_figure=True)

    # --- List your WAV files here (Title, GitHub URL) ---
    wav_files = [
        ("Dolphin speech (WAV)", "https://github.com/MK316/english-phonetics/blob/main/pages/audio/dolphin.wav"),
        ("Human speech (WAV)", "https://github.com/MK316/english-phonetics/blob/main/pages/audio/human.wav"),
        # Add more...
    ]

    for title, gh_url in wav_files:
        raw_url = to_raw(gh_url)
        st.markdown(f"**{title}**")
        # Player
        st.audio(raw_url, format="audio/wav")
        # Waveform
        try:
            data_bytes = fetch_bytes(raw_url)
            y, sr = load_wav_from_bytes(data_bytes)
            plot_waveform(y, sr, f"{title} — waveform")
        except Exception as e:
            st.caption(f"Waveform preview failed: {e}")


# https://github.com/MK316/english-phonetics/blob/main/pages/audio/dolphin.wav

# ================== Tips ==================
# - Each widget uses a unique key (e.g., app1_text) to avoid conflicts across tabs/pages.
# - Use st.form for groups of inputs you want to submit together.
# - For bigger apps per tab, factor logic into functions and call them inside the tab blocks.
# - You can add a common sidebar for shared settings across all tabs if needed.
