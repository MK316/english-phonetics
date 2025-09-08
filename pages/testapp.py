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
# Fields per item:
#   word: orthographic form
#   ipa: phonemic transcription (no length colon)
#   feedback: guidance shown to learners
# =========================
DATASET: List[Dict[str, str]] = [
    {
        "word": "language",
        "ipa": "ˈlæŋɡwɪdʒ",   # no ː
        "feedback": "Note the cluster /ŋɡ/ and the affricate /dʒ/ at the end.",
    },
    {
        "word": "linguistics",
        "ipa": "lɪŋˈɡwɪstɪks",  # no ː
        "feedback": "Pay attention to /ŋɡw/ cluster; no long-vowel marks are used.",
    },
]

# =========================
# Helpers
# =========================
def ensure_state():
    # Per-tab indices
    if "idx_tab1" not in st.session_state:
        st.session_state.idx_tab1 = random.randrange(len(DATASET))
    if "idx_tab2" not in st.session_state:
        st.session_state.idx_tab2 = random.randrange(len(DATASET))

    if "typed_answer" not in st.session_state:
        st.session_state.typed_answer = ""

    if "show_feedback_tab1" not in st.session_state:
        st.session_state.show_feedback_tab1 = False

    if "result_tab2" not in st.session_state:
        st.session_state.result_tab2 = None  # ("correct"/"wrong", message)

ensure_state()


def pick_new_random(old_idx: int, n: int) -> int:
    if n <= 1:
        return 0
    pool = [i for i in range(n) if i != old_idx]
    return random.choice(pool)


def sine_beep_wav_bytes(freq=440.0, seconds=0.7, samplerate=16000, volume=0.3) -> bytes:
    """Small in-memory mono WAV as a fallback if TTS fails."""
    t = np.linspace(0, seconds, int(samplerate * seconds), endpoint=False)
    wave_data = (volume * np.sin(2 * math.pi * freq * t)).astype(np.float32)
    data_int16 = (wave_data * 32767.0).astype(np.int16)

    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)         # 16-bit
        wf.setframerate(samplerate)
        wf.writeframes(data_int16.tobytes())
    bio.seek(0)
    return bio.read()


@st.cache_data(show_spinner=False)
def gtts_bytes(text: str, lang: str = "en") -> bytes:
    """Synthesize TTS via gTTS and return MP3 bytes. Cached for speed."""
    from gtts import gTTS
    bio = io.BytesIO()
    gTTS(text=text, lang=lang, slow=False).write_to_fp(bio)
    bio.seek(0)
    return bio.read()


def audio_for_word(word: str) -> Tuple[str, bytes]:
    """
    Return ("mp3", bytes) if gTTS succeeds, else ("wav", beep_bytes).
    """
    try:
        mp3 = gtts_bytes(word, lang="en")
        return "mp3", mp3
    except Exception:
        # Fallback: simple beep
        return "wav", sine_beep_wav_bytes()


def normalize_phonemic(s: str) -> str:
    """
    Normalize student's typed phonemic transcription:
    - NFKC normalization
    - remove slashes/brackets, whitespace
    - remove stress marks (ˈ, ˌ) and length (ː, :)
    - map ASCII 'g' → IPA 'ɡ'
    - unify common affricate variants
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)

    for ch in "/[](){} \t\n\r":
        s = s.replace(ch, "")

    for ch in ["ˈ", "ˌ", "ː", ":"]:
        s = s.replace(ch, "")

    # Common equivalences
    s = s.replace("ʤ", "dʒ")   # alt affricate
    s = s.replace("t͡ʃ", "tʃ")  # tie-bar variant

    # ASCII 'g' to IPA 'ɡ'
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
        msg = (
            "❌ Not quite.\n\n"
            f"**Your input (normalized):** `{user_norm}`\n\n"
            f"**Target:** `{target_norm}`"
        )
        return False, msg


# =========================
# TABS
# =========================
tab1, tab2 = st.tabs(["Tab 1 — Read the transcription", "Tab 2 — Type after listening"])

# ---------- TAB 1 ----------
with tab1:
    st.subheader("Read the transcription while listening")

    item = DATASET[st.session_state.idx_tab1]
    fmt, audio_bytes = audio_for_word(item["word"])

    st.write(f"**Word:** {item['word']}")
    st.write(f"**Phonemic transcription:** /{item['ipa']}/  *(No long-vowel colon)*")

    if fmt == "mp3":
        st.audio(audio_bytes, format="audio/mp3")
    else:
        st.audio(audio_bytes, format="audio/wav")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔁 New item", key="t1_new"):
            st.session_state.idx_tab1 = pick_new_random(st.session_state.idx_tab1, len(DATASET))
            st.session_state.show_feedback_tab1 = False
            st.rerun()  # one click, immediate refresh
    with c2:
        if st.button("💡 Show feedback", key="t1_fb"):
            st.session_state.show_feedback_tab1 = True

    if st.session_state.show_feedback_tab1:
        st.info(item["feedback"])

# ---------- TAB 2 ----------
with tab2:
    st.subheader("Type the transcription after listening")

    item2 = DATASET[st.session_state.idx_tab2]
    fmt2, audio_bytes2 = audio_for_word(item2["word"])

    # Optionally hide the word by commenting the next line
    st.write(f"**Word:** {item2['word']}")

    if fmt2 == "mp3":
        st.audio(audio_bytes2, format="audio/mp3")
    else:
        st.audio(audio_bytes2, format="audio/wav")

    st.text_input(
        "Type the phonemic transcription (no long-vowel colon):",
        key="typed_answer",
        placeholder="e.g., /lɪŋˈɡwɪstɪks/",
    )

    colA, colB, colC = st.columns([1, 1, 1])
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
        "- Edit the `DATASET` list near the top of this file.\n"
        "- Use **phonemic** transcription without long-vowel colons (e.g., `ˈlæŋɡwɪdʒ`).\n"
        "- The app generates audio with **gTTS** for the word string.\n"
    )
