# transcription_practice_from_github.py
# Run: streamlit run transcription_practice_from_github.py

import io
import math
import random
import unicodedata
import wave
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="Transcription Practice (GitHub CSV)", layout="centered")
st.title("🎧 Transcription Practice (GitHub CSV)")

st.caption(
    "Provide a GitHub **RAW** CSV URL with columns: "
    "**Word**, **Phonemic Transcription**, **Phonetic Transcription**, **Feedback**.\n\n"
    "Tab 1: Read the transcription while listening, then type the **word**.\n"
    "Tab 2: Listen first, then type the **phonemic** transcription (no long-vowel colon)."
)

# ---------------- RAW URL input (edit this default for your repo) ----------------
DEFAULT_RAW_URL = "https://raw.githubusercontent.com/MK316/english-phonetics/refs/heads/main/pages/data/IPAdata1.csv"  # e.g., "https://raw.githubusercontent.com/MK316/classmaterial/refs/heads/main/Phonetics/transcription_items.csv"
raw_url = st.text_input("GitHub RAW CSV URL", value=DEFAULT_RAW_URL, placeholder="https://raw.githubusercontent.com/MK316/english-phonetics/refs/heads/main/pages/data/IPAdata1.csv")

# ---------------- Sample fallback dataset ----------------
SAMPLE_DF = pd.DataFrame(
    [
        {
            "Word": "language",
            "Phonemic Transcription": "ˈlæŋɡwɪdʒ",
            "Phonetic Transcription": "ˈlæŋɡwɪdʒ",
            "Feedback": "Focus on /ŋɡ/ and final /dʒ/.",
        },
        {
            "Word": "linguistics",
            "Phonemic Transcription": "lɪŋˈɡwɪstɪks",
            "Phonetic Transcription": "lɪŋˈɡwɪstɪks",
            "Feedback": "Mind the /ŋɡw/ cluster; no length marks.",
        },
    ]
)
REQUIRED_COLS = {"Word", "Phonemic Transcription", "Phonetic Transcription", "Feedback"}

@st.cache_data(show_spinner=False)
def load_csv_from_url(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)
    if not REQUIRED_COLS.issubset(set(df.columns)):
        missing = REQUIRED_COLS - set(df.columns)
        raise ValueError(f"CSV is missing columns: {', '.join(missing)}")
    df = df.dropna(subset=["Word", "Phonemic Transcription"]).reset_index(drop=True)
    df["Feedback"] = df["Feedback"].fillna("")
    return df

# Try loading from URL or fall back to sample
if raw_url.strip():
    try:
        DF = load_csv_from_url(raw_url.strip())
        st.success(f"Loaded {len(DF)} items from URL.")
    except Exception as e:
        st.error(f"Could not load CSV from URL: {e}")
        DF = SAMPLE_DF.copy()
        st.info("Using the built-in sample instead.")
else:
    DF = SAMPLE_DF.copy()
    st.info("No URL provided. Using a small built-in sample.")

# Build dataset records
DATASET: List[Dict[str, str]] = [
    {
        "word": row["Word"],
        "phonemic": row["Phonemic Transcription"],
        "phonetic": row["Phonetic Transcription"],
        "feedback": row["Feedback"],
    }
    for _, row in DF.iterrows()
]

if not DATASET:
    st.error("No items available. Check your CSV content.")
    st.stop()

# ---------------- Audio helpers (gTTS) ----------------
def sine_beep_wav_bytes(freq=440.0, seconds=0.7, samplerate=16000, volume=0.3) -> bytes:
    t = np.linspace(0, seconds, int(samplerate * seconds), endpoint=False)
    wave_data = (volume * np.sin(2 * math.pi * freq * t)).astype(np.float32)
    data_int16 = (wave_data * 32767.0).astype(np.int16)
    bio = io.BytesIO()
    with wave.open(bio, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(samplerate)
        wf.writeframes(data_int16.tobytes())
    bio.seek(0)
    return bio.read()

@st.cache_data(show_spinner=False)
def gtts_bytes(text: str, lang: str = "en") -> bytes:
    from gtts import gTTS
    bio = io.BytesIO()
    gTTS(text=text, lang=lang, slow=False).write_to_fp(bio)
    bio.seek(0)
    return bio.read()

def audio_for_word(word: str) -> Tuple[str, bytes]:
    try:
        mp3 = gtts_bytes(word, lang="en")
        return "mp3", mp3
    except Exception:
        return "wav", sine_beep_wav_bytes()

# ---------------- State ----------------
def ensure_state():
    # dataset size guard
    st.session_state.setdefault("n_items", len(DATASET))
    if st.session_state.n_items != len(DATASET):
        st.session_state.n_items = len(DATASET)
        st.session_state["idx_tab1"] = 0
        st.session_state["idx_tab2"] = 0

    # indices
    st.session_state.setdefault("idx_tab1", 0)
    st.session_state.setdefault("idx_tab2", 0)

    # Tab 1
    st.session_state.setdefault("t1_typed_word", "")
    st.session_state.setdefault("t1_word_result", None)  # ("correct"/"wrong", message)

    # Tab 2
    st.session_state.setdefault("typed_answer", "")
    st.session_state.setdefault("result_tab2", None)     # ("correct"/"wrong", message)

ensure_state()

def pick_new_random(old_idx: int, n: int) -> int:
    if n <= 1:
        return 0
    pool = [i for i in range(n) if i != old_idx]
    return random.choice(pool)

# ---------------- Normalization & checking ----------------
def normalize_word(s: str) -> str:
    if not s:
        return ""
    s = s.strip().lower()
    for ch in " -_'’":
        s = s.replace(ch, "")
    return s

def compare_word(user_word: str, target_word: str) -> bool:
    return normalize_word(user_word) == normalize_word(target_word)

def normalize_phonemic(s: str) -> str:
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

def compare_transcription(user_input: str, target_phonemic: str) -> bool:
    return normalize_phonemic(user_input) == normalize_phonemic(target_phonemic)

# ---------------- Button callbacks ----------------
def t1_new_item():
    st.session_state.idx_tab1 = pick_new_random(st.session_state.idx_tab1, len(DATASET))
    st.session_state.t1_typed_word = ""
    st.session_state.t1_word_result = None

def t1_check_word():
    item = DATASET[st.session_state.idx_tab1]
    ok = compare_word(st.session_state.t1_typed_word, item["word"])
    st.session_state.t1_word_result = ("correct" if ok else "wrong",
                                       "Correct" if ok else (item["feedback"] or "Try again."))

def t1_clear():
    st.session_state.t1_typed_word = ""
    st.session_state.t1_word_result = None

def t2_check():
    item = DATASET[st.session_state.idx_tab2]
    ok = compare_transcription(st.session_state.typed_answer, item["phonemic"])
    st.session_state.result_tab2 = ("correct" if ok else "wrong",
                                    "Correct" if ok else (item["feedback"] or "Listen again and try the phonemic form."))

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
    st.write(f"**Phonemic transcription:** /{item['phonemic']}/  *(No long-vowel colon)*")
    st.caption(f"Phonetic transcription: [{item['phonetic']}]")
    st.audio(audio_bytes, format=f"audio/{fmt}")

    st.text_input("Type the word (orthographic):", key="t1_typed_word", placeholder="e.g., language")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("✅ Check word", key="t1_check", on_click=t1_check_word)
    with c2:
        st.button("🧹 Clear", key="t1_clear", on_click=t1_clear)
    with c3:
        st.button("🔁 New item", key="t1_new", on_click=t1_new_item)

    if st.session_state.t1_word_result:
        status, msg = st.session_state.t1_word_result
        (st.success if status == "correct" else st.error)(msg)

# ===== TAB 2 =====
with tab2:
    st.subheader("Type the transcription after listening")

    item2 = DATASET[st.session_state.idx_tab2]
    fmt2, audio_bytes2 = audio_for_word(item2["word"])

    st.write(f"**Word:** {item2['word']}")
    st.audio(audio_bytes2, format=f"audio/{fmt2}")

    st.text_input(
        "Type the **phonemic transcription** (no long-vowel colon):",
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

# --------------- Footer ---------------
st.caption(f"Dataset items: {len(DATASET)}")
