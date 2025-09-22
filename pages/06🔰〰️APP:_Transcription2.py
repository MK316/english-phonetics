import streamlit as st
from gtts import gTTS
from io import BytesIO

# ---------------- Page setup ----------------
st.set_page_config(page_title="IPA Transcription – Audio Practice", layout="centered")
st.title("🔈 Transcription Practice – Audio Player")

# ---------------- Practice list (20 items) ----------------
PRACTICE_ITEMS = [
    # single words
    "butter", "better", "apple", "father", "water",
    "paper", "Christmas", "student", "quickly", "music",
    # short phrases
    "a cup of tea", "let it be", "want to go", "going to school", "sit down",
    "black cat", "you and me", "this year", "good morning", "see you later",
]

# ---------------- Helper ----------------
def synthesize_gtts(text: str) -> bytes:
    """Return MP3 audio bytes for the given text using gTTS."""
    tts = gTTS(text=text, lang="en", slow=False)
    buf = BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)
    return buf.read()

# ---------------- Show audio players ----------------
st.markdown("### 🎧 Click play to listen")

for item in PRACTICE_ITEMS:
    audio_bytes = synthesize_gtts(item)
    st.markdown(f"**{item}**")
    st.audio(audio_bytes, format="audio/mp3")
    st.divider()
