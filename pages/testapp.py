# transcription_practice.py
# Run: streamlit run transcription_practice.py

import io
import math
import random
import unicodedata
import wave
from typing import Dict, List, Optional, Tuple

import numpy as np
import streamlit as st

# =========================
# Page setup
# =========================
st.set_page_config(page_title="Transcription Practice", layout="centered")
st.title("🎧 Transcription Practice")

st.caption(
    "Tab 1: Read the phonemic transcription while listening.\n\n"
    "Tab 2: Listen, then type the **phonemic** transcription (no long-vowel colon)."
)

# =========================
# Sample dataset (replace later)
# Fields:
#   word: orthographic form
#   ipa: target phonemic transcription (no length colon)
#   audio_url: if you have hosted audio, put a direct URL; leave '' to use the built-in beep
#   feedback: short tip shown on feedback
# =========================
DATASET: List[Dict[str, str]] = [
    {
        "word": "language",
        "ipa": "ˈlæŋɡwɪdʒ",  # no ː colons, phonemic
        "audio_url": "",       # replace with your real URL later
        "feedback": "Note the cluster /ŋɡ/ and the affricate /dʒ/ at the end.",
    },
    {
        "word": "linguistics",
        "ipa": "lɪŋˈɡwɪstɪks",  # no ː colons, phonemic
        "audio_url": "",         # replace with your real URL later
        "feedback": "Pay attention to /ŋɡw/ cluster; no long-vowel marks are used.",
    },
]

# =========================
# Helpers
# =========================
def ensure_state():
    # Per-tab current index
    if "idx_tab1" not in st.session_state:
        st.session_state.idx_tab1 = random.randrange(len(DATASET))
    if "idx_tab2" not in st.session_state:
        st.session_state.idx_tab2 = random.randrange(len(DATASET))

    # For tab2 answers
    if "typed_answer" not in st.session_state:
        st.session_state.typed_answer = ""

    # Feedback toggles
    if "show_feedback_tab1" not in st.session_state:
        st.session_state.show_feedback_tab1 = False
    if "result_tab2" not in st.session_state:
        st.session_state.result_tab2 = None  # ("correct"/"wrong", message)

ensure_state()


def pick_new_random(old_idx: int, n: int) -> int:
    if n <= 1:
        return 0
    # try to avoid immediate repetition
    choices = [i for i in range(n) if i != old_idx]
    return random.choice(choices)


def sine_beep_wav_bytes(freq=440.0, seconds=0.7, samplerate=16000, volume=0.3) -> bytes:
    """
    Make a small WAV in-memory (mono) so audio always plays even if no URL is provided.
    """
    t = np.linspace(0, seconds, int(samplerate * seconds), endpoint=False)
    wave_data = (volume * np.sin(2 * math.pi * freq * t)).astype(np.float32)

    # Convert to 16-bit PCM
    data_int16 = (wave_data * 32767.0).astype(np.int16)

    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)         # 16-bit
        wf.setframerate(samplerate)
        wf.writeframes(data_int16.tobytes())
    bio.seek(0)
    return bio.read()


def audio_source(item: Dict[str, str]) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Return either (url, None) if url exists, else (None, wav_bytes) as fallback.
    """
    url = item.get("audio_url", "").strip()
    if url:
        return url, None
    return None, sine_beep_wav_bytes()


def normalize_phonemic(s: str) -> str:
    """
    Normalize user's typed phonemic transcription:
    - NFKC normalization
    - remove slashes/brackets, spaces, and stress marks
    - remove long-vowel colon if present (shouldn't be, but we accept and ignore)
    - map ASCII 'g' to IPA 'ɡ'
    - map 'ʤ' -> 'dʒ', 't͡ʃ' -> 'tʃ'
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    # Remove delimiters and whitespace
    for ch in "/[](){} \t\n\r":
        s = s.replace(ch, "")
    # Remove stress / length marks
    for ch in ["ˈ", "ˌ", "ː", ":"]:
        s = s.replace(ch, "")
    # Common equivalences
    s = s.replace("ʤ", "dʒ")   # alt affricate glyph
    s = s.replace("t͡ʃ", "tʃ")  # tie-bar variant
    # Map ASCII g to IPA ɡ (if user typed 'g')
    # Careful to not clobber 'ŋɡ' etc; do a simple char replace
    s = s.replace("g", "ɡ")
    return s


def canonical_target(item: Dict[str, str]) -> str:
    """Canonical normalized target to compare against."""
    return normalize_phonemic(item["ipa"])


def compare_transcription(user_input: str, item: Dict[str, str]) -> Tuple[bool, str]:
    """
    Return (is_correct, message).
    """
    user_norm = normalize_phonemic(user_input)
    target_norm = canonical_target(item)

    if user_norm == target_norm:
        return True, "✅ Correct!"
    else:
        # Provide simple diff style: show what we received vs target (normalized)
        msg = f"❌ Not quite.\n\n**Your input (norm):** `{user_norm}`\n\n**Target:** `{target_norm}`"
        return False, msg


# =========================
# TABS
# =========================
tab1, tab2 = st.tabs(["Tab 1 — Read the transcription", "Tab 2 — Type after listening"])

# ---------- TAB 1 ----------
with tab1:
    st.subheader("Read the transcription while listening")

    item = DATASET[st.session_state.idx_tab1]
    url, wav_bytes = audio_source(item)

    st.write(f"**Word:** {item['word']}")
    st.write(f"**Phonemic transcription:** /{item['ipa']}/  *(No long-vowel colon)*")

    # Audio
    if url:
        st.audio(url, format="audio/mp3")
    else:
        st.audio(wav_bytes, format="audio/wav")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔁 New item", key="t1_new"):
            st.session_state.idx_tab1 = pick_new_random(st.session_state.idx_tab1, len(DATASET))
            st.session_state.show_feedback_tab1 = False
            st.rerun()
    with c2:
        if st.button("💡 Show feedback", key="t1_fb"):
            st.session_state.show_feedback_tab1 = True

    if st.session_state.show_feedback_tab1:
        st.info(item["feedback"])

# ---------- TAB 2 ----------
with tab2:
    st.subheader("Type the transcription after listening")

    item2 = DATASET[st.session_state.idx_tab2]
    url2, wav_bytes2 = audio_source(item2)

    # Audio only (don't show the IPA here)
    st.write(f"**Word:** {item2['word']}")  # if you want to hide the word, comment this out
    if url2:
        st.audio(url2, format="audio/mp3")
    else:
        st.audio(wav_bytes2, format="audio/wav")

    # Input
    st.text_input(
        "Type the phonemic transcription (no long-vowel colon):",
        key="typed_answer",
        placeholder="e.g., /lɪŋˈɡwɪstɪks/",
    )

    colA, colB, colC = st.columns([1,1,1])
    with colA:
        if st.button("✅ Check", key="t2_check"):
            ok, msg = compare_transcription(st.session_state.typed_answer, item2)
            st.session_state.result_tab2 = ("correct" if ok else "wrong", msg)
    with colB:
        if st.button("🧹 Clear", key="t2_clear"):
            st.session_state.typed_answer = ""
            st.session_state.result_tab2 = None
            st.rerun()
    with colC:
        if st.button("🔁 New item", key="t2_new"):
            st.session_state.idx_tab2 = pick_new_random(st.session_state.idx_tab2, len(DATASET))
            st.session_state.typed_answer = ""
            st.session_state.result_tab2 = None
            st.rerun()

    # Feedback
    if st.session_state.result_tab2:
        status, msg = st.session_state.result_tab2
        if status == "correct":
            st.success(msg)
        else:
            st.error(msg)

# =========================
# Notes for replacing dataset
# =========================
with st.expander("ℹ️ How to replace the sample dataset"):
    st.markdown(
        """
        The app reads the in-code `DATASET` list (near the top).  
        Each item needs:
        - `word`: orthographic form
        - `ipa`: phonemic transcription **without long-vowel colons** (e.g., `ˈlæŋɡwɪdʒ`)
        - `audio_url`: direct URL to an audio file (mp3/wav). If empty, the app plays a short beep.
        - `feedback`: short tip string

        Example:
        ```python
        DATASET = [
            {"word": "language", "ipa": "ˈlæŋɡwɪdʒ", "audio_url": "https://.../language.mp3",
             "feedback": "Note the cluster /ŋɡ/ and the affricate /dʒ/."},
            {"word": "linguistics", "ipa": "lɪŋˈ
