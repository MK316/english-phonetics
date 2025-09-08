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

# ---------------- Page setup ----------------
st.set_page_config(page_title="Transcription Practice", layout="centered")
st.title("🎧 Transcription Practice")

st.caption(
    "Tab 1: Read the **phonemic** transcription while listening, then type the word you hear.\n\n"
    "Tab 2: Listen first, then type the **phonemic** transcription (no long-vowel colon)."
)

# ---------------- Sample dataset (replace later) ----------------
# Fields per item:
#   word: orthographic form
#   ipa: phonemic transcription (no length colon)
#   feedback: short hint
DATASET: List[Dict[str, str]] = [
    {"word": "language",    "ipa": "ˈlæŋɡwɪdʒ",   "feedback": "Note /ŋɡ/ and final /dʒ/; no length marks."},
    {"word": "linguistics", "ipa": "lɪŋˈɡwɪstɪks", "feedback": "Mind the /ŋɡw/ cluster and secondary syllables."},
]

# ---------------- Helpers: state & utilities ----------------
def ensure_state():
    st.session_state.setdefault("idx_tab1", random.randrange(len(DATASET)))
    st.session_state.setdefault("idx_tab2", random.randrange(len(DATASET)))

    # Tab 1 (word typing)
    st.session_state.setdefault("t1_typed_word", "")
    st.session_state.setdefault("t1_word_result", None)  # ("correct"/"wrong", message)
    st.session_state.setdefault("t1_show_feedback", False)

    # Tab 2 (IPA typing)
    st.session_state.setdefault("typed_answer", "")
    st.session_state.setdefault("result_tab2", None)     # ("correct"/"wrong", message)

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
    """Return ('mp3', bytes) if gTTS succeeds, else ('wav', beep_bytes)."""
    try:
        mp3 = gtts_bytes(word, lang="en")
        return "mp3", mp3
    except Exception:
        return "wav", sine_beep_wav_bytes()


# ---------------- Normalization & checking ----------------
def normalize_phonemic(s: str) -> str:
    """
    Normalize user IPA:
    - NFKC
    - remove slashes/brackets/whitespace
    - remove stress (ˈ, ˌ) & length (ː, :)
    - unify affricates: ʤ->dʒ, t͡ʃ->tʃ
    - ASCII g -> IPA ɡ
    """
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)

    for ch in "/[](){} \t\n\r":
        s = s.replace(ch, "")
    for ch in ["ˈ", "ˌ", "ː", ":"]:
        s = s.replace(ch, "")

    s = s.replace("ʤ", "dʒ")
    s = s.replace("t͡ʃ", "tʃ")
    s = s.replace("g", "ɡ")
    return s


def canonical_target_ipa(item: Dict[str, str]) -> str:
    return normalize_phonemic(item["ipa"])


def compare_transcription(user_input: str, item: Dict[str, str]) -> Tuple[bool, str]:
    user_norm = normalize_phonemic(user_input)
    target_norm = canonical_target_ipa(item)
    if user_norm == target_norm:
        return True, "✅ Correct!"
    return False, f"❌ Not quite.\n\n**Your input (normalized):** `{user_norm}`\n\n**Target:** `{target_norm}`"


def normalize_word(s: str) -> str:
    """Lowercase, strip spaces/punctuation (simple) for word-typing check."""
    if not s:
        return ""
    s = s.strip().lower()
    # Remove trivial spaces/dashes/quotes
    for ch in " -_'’":
        s = s.replace(ch, "")
    return s


def compare_word(user_word: str, item: Dict[str, str]) -> Tuple[bool, str]:
    if normalize_word(user_word) == normalize_word(item["word"]):
        return True, "✅ Correct!"
    return False, f"❌ Not quite. Target word: **{item['word']}**"


# ---------------- Button callbacks (one-click) ----------------
def t1_new_item():
    st.session_state.idx_tab1 = pick_new_random(st.session_state.idx_tab1, len(DATASET))
    st.session_state.t1_typed_word = ""
    st.session_state.t1_word_result = None
    st.session_state.t1_show_feedback = False

def t1_check_word():
    item = DATASET[st.session_state.idx_tab1]
    ok, msg = compare_word(st.session_state.t1_typed_word, item)
    st.session_state.t1_word_result = ("correct" if ok else "wrong", msg)

def t1_clear():
    st.session_state.t1_typed_word = ""
    st.session_state.t1_word_result = None

def t1_show_fb():
    st.session_state.t1_show_feedback = True

def t2_check():
    item = DATASET[st.session_state.idx_tab2]
    ok, msg = compare_transcription(st.session_state.typed_answer, item)
    st.session_state.result_tab2 = ("correct" if ok else "wrong", msg)

def t2_clear():
    st.session_state.typed_answer = ""
    st.session_state.result_tab2 = None

def t2_new_item():
    st.session_state.idx_tab2 = pick_new_random(st.session_state.idx_tab2, len(DATASET))
    st.session_state.typed_answer = ""
    st.session_state.result_tab2 = None


# ---------------- Tabs ----------------
tab1, tab2 = st.tabs(["Tab 1 — Read the transcription", "Tab 2 — Type after listening"])

# ===== TAB 1 =====
with tab1:
    st.subheader("Read the transcription while listening")

    item = DATASET[st.session_state.idx_tab1]
    fmt, audio_bytes = audio_for_word(item["word"])

    st.write(f"**Word:** {item['word']}")
    st.write(f"**Phonemic transcription:** /{item['ipa']}/  *(No long-vowel colon)*")

    st.audio(audio_bytes, format=f"audio/{fmt}")

    # Type the word you hear/see
    st.text_input(
        "Type the word (orthographic):",
        key="t1_typed_word",
        placeholder="e.g., language",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("✅ Check word", key="t1_check", on_click=t1_check_word)
    with c2:
        st.button("🧹 Clear", key="t1_clear", on_click=t1_clear)
    with c3:
        st.button("🔁 New item", key="t1_new", on_click=t1_new_item)

    # Feedback controls
    st.button("💡 Show feedback", key="t1_fb", on_click=t1_show_fb)

    # Results
    if st.session_state.t1_word_result:
        status, msg = st.session_state.t1_word_result
        (st.success if status == "correct" else st.error)(msg)

    if st.session_state.t1_show_feedback:
        st.info(item["feedback"])

# ===== TAB 2 =====
with tab2:
    st.subheader("Type the transcription after listening")

    item2 = DATASET[st.session_state.idx_tab2]
    fmt2, audio_bytes2 = audio_for_word(item2["word"])

    # Optionally hide the word by commenting the next line
    st.write(f"**Word:** {item2['word']}")
    st.audio(audio_bytes2, format=f"audio/{fmt2}")

    st.text_input(
        "Type the phonemic transcription (no long-vowel colon):",
        key="typed_answer",
        placeholder="e.g., /lɪŋˈɡwɪstɪks/",
    )

    colA, colB, colC = st.columns(3)
    with colA:
        st.button("✅ Check", key="t2_check_btn", on_click=t2_check)
    with colB:
        st.button("🧹 Clear", key="t2_clear_btn", on_click=t2_clear)
    with colC:
        st.button("🔁 New item", key="t2_new_btn", on_click=t2_new_item)

    if st.session_state.result_tab2:
        status, msg = st.session_state.result_tab2
        (st.success if status == "correct" else st.error)(msg)

# ---------------- Notes ----------------
with st.expander("ℹ️ Replace the dataset"):
    st.markdown(
        "- Edit the `DATASET` list near the top of this file.\n"
        "- Use **phonemic** transcription without length colons (e.g., `ˈlæŋɡwɪdʒ`).\n"
        "- Audio is generated with **gTTS** for the *word string*.\n"
    )
