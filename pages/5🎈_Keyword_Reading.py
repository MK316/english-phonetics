import re
from datetime import datetime
import pandas as pd
import streamlit as st
import io
import requests

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Passage Blank Practice", layout="wide")

# ✅ Your GitHub RAW CSV URL
CSV_URL = "https://raw.githubusercontent.com/MK316/english-phonetics/refs/heads/main/pages/readings/readingquiz001a.csv"

# =========================
# HELPERS
# =========================
BLANK10_HTML = '<span style="font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;">__________</span>'

def normalize_text(s: str) -> str:
    """Lowercase + keep letters/apostrophes + single-space."""
    s = str(s).strip().lower()
    s = re.sub(r"[^a-zA-Z'\s]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def parse_correct_answers(ans_cell: str) -> list[list[str]]:
    items = [a.strip() for a in str(ans_cell).split(",") if a.strip()]
    out: list[list[str]] = []
    for item in items:
        words = re.findall(r"[A-Za-z']+", item)
        out.append(words if words else item.split())
    return out

def render_passage_with_numbered_blanks(passage: str, correct_items: list[list[str]]) -> str:
    replacements = []
    for i, words in enumerate(correct_items, start=1):
        n = max(1, len(words))
        blanks = " ".join([BLANK10_HTML] * n)
        replacements.append(f'<b>({i})</b> {blanks}')

    pattern = r"_{2,}"
    matches = list(re.finditer(pattern, str(passage)))

    out = []
    last = 0
    for idx, m in enumerate(matches):
        out.append(passage[last:m.start()])
        out.append(replacements[idx] if idx < len(replacements) else BLANK10_HTML)
        last = m.end()
    out.append(passage[last:])
    return "".join(out).replace("\n", "<br>")

def expected_flat_list(correct_items: list[list[str]]) -> list[str]:
    exp = []
    for words in correct_items:
        for w in words:
            exp.append(normalize_text(w))
    return exp

@st.cache_data(show_spinner=False)
def load_data(url: str) -> pd.DataFrame:
    r = requests.get(url)
    df = pd.read_csv(io.BytesIO(r.content))
    col_map = {}
    for c in df.columns:
        cc = c.strip().lower()
        if cc == "chapter": col_map[c] = "Chapter"
        elif cc == "passage": col_map[c] = "Passage"
        elif cc in ("correct answers", "correct_answers", "answers", "correct answer"):
            col_map[c] = "Correct answers"
    df = df.rename(columns=col_map)
    df["Chapter"] = df["Chapter"].astype(str).str.strip()
    df["_row"] = range(len(df))
    df = df.sort_values(["Chapter", "_row"], ignore_index=True).drop(columns=["_row"])
    return df

# =========================
# STATE & CALLBACKS
# =========================
def clear_answers_callback():
    """Triggered when selectboxes change to wipe inputs and reset 'started' status."""
    for k in list(st.session_state.keys()):
        if k.startswith("ans_"):
            del st.session_state[k]
    st.session_state.started = False
    st.session_state.submitted = False
    st.session_state.last_results = None

def init_state():
    defaults = {
        "started": False,
        "start_time": None,
        "chapter": None,
        "passage_no": None,
        "row_idx": None,
        "submitted": False,
        "attempts": 0,
        "last_results": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =========================
# UI - SIDEBAR
# =========================
try:
    df = load_data(CSV_URL)
except Exception as e:
    st.error("Failed to load CSV.")
    st.stop()

chapters = sorted(df["Chapter"].dropna().unique().tolist())

with st.sidebar:
    st.header("⚙️ Settings")
    chapter = st.selectbox("Chapter", chapters, index=0, key="chapter_select", on_change=clear_answers_callback)
    
    sub_df = df[df["Chapter"] == chapter].reset_index(drop=False)
    passage_numbers = list(range(1, len(sub_df) + 1))
    passage_no = st.selectbox("Passage number", passage_numbers, index=0, key="passage_select", on_change=clear_answers_callback)
    
    st.divider()
    c_start, c_reset = st.columns(2)
    start_btn = c_start.button("✅ Start", use_container_width=True)
    if c_reset.button("🔄 Reset All", use_container_width=True):
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.rerun()

# =========================
# LOGIC
# =========================
if start_btn:
    st.session_state.started = True
    st.session_state.start_time = datetime.now()
    st.session_state.chapter = chapter
    st.session_state.passage_no = passage_no
    row = sub_df.iloc[passage_no - 1]
    st.session_state.row_idx = int(row["index"])
    st.session_state.submitted = False
    st.session_state.last_results = None
    # Ensure fresh start for answers
    for k in list(st.session_state.keys()):
        if k.startswith("ans_"): del st.session_state[k]

# =========================
# MAIN CONTENT
# =========================
st.title("📘 Reading with keywords")

if not st.session_state.started or st.session_state.row_idx is None:
    st.info("🍄 👈 Select a Chapter and Passage from the sidebar, then click **Start** button there.")
    st.stop()

row = df.loc[st.session_state.row_idx]
correct_items = parse_correct_answers(row["Correct answers"])
expected = expected_flat_list(correct_items)

st.markdown(f"## {st.session_state.chapter} · Passage {st.session_state.passage_no}")
passage_html = render_passage_with_numbered_blanks(row["Passage"], correct_items)

st.markdown(f'<div style="line-height:1.8; font-size:1.1rem; background:#f9f9f9; padding:20px; border-radius:10px; border:1px solid #eee;">{passage_html}</div>', unsafe_allow_html=True)

st.markdown("### Your Answers")

with st.form("answer_form", clear_on_submit=False):
    ans_flat = []
    input_idx = 0
    for blank_no, words in enumerate(correct_items, start=1):
        n = max(1, len(words))
        l_col, i_col = st.columns([1, 8])
        l_col.markdown(f"**({blank_no})**")
        
        # Determine how many columns to create for inputs
        cols = i_col.columns([1] * n + [2]) # dynamic columns based on word count
        for i in range(n):
            val = cols[i].text_input(
                f"b{blank_no}w{i}",
                key=f"ans_{input_idx}",
                label_visibility="collapsed",
                placeholder=f"Word {i+1}" if n > 1 else "Type here"
            )
            ans_flat.append(val)
            input_idx += 1
            
    submit = st.form_submit_button("📌 Submit Answers", use_container_width=True)

if submit:
    st.session_state.attempts += 1
    user_norm = [normalize_text(a) for a in ans_flat]
    results = [u == e for u, e in zip(user_norm, expected)]
    st.session_state.submitted = True
    st.session_state.last_results = results
    st.session_state.finish_time = datetime.now()

# FEEDBACK
if st.session_state.submitted:
    results = st.session_state.last_results
    correct_n = sum(results)
    total = len(results)
    
    if correct_n == total:
        st.success(f"🎉 Perfect Score! {correct_n} / {total}")
    else:
        st.warning(f"✍️ Score: {correct_n} / {total}")
    
    with st.expander("Review Correct Answers"):
        for blank_no, words in enumerate(correct_items, start=1):
            st.write(f"**({blank_no})** {' '.join(words)}")
