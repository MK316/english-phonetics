import re
from datetime import datetime

import pandas as pd
import streamlit as st

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Passage Blank Practice", layout="wide")

# ✅ Replace this with your GitHub RAW CSV URL
# Example:
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
    """
    Cell format: answers separated by commas
    - each answer can be one or multiple words
    Returns: list of list of words, e.g. [["phonetics"], ["more", "intelligibly"], ["described"]]
    """
    items = [a.strip() for a in str(ans_cell).split(",") if a.strip()]
    out: list[list[str]] = []
    for item in items:
        words = re.findall(r"[A-Za-z']+", item)
        out.append(words if words else item.split())
    return out

def render_passage_with_numbered_blanks(passage: str, correct_items: list[list[str]]) -> str:
    """
    Replace ALL underline runs (__, ___, ______, etc.) with numbered 10-underscore blanks.
    Multi-word answers become multiple blanks under the same number.
    Example: (2) __________ __________
    """
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

    # preserve line breaks nicely in HTML
    rendered = "".join(out).replace("\n", "<br>")
    return rendered

def expected_flat_list(correct_items: list[list[str]]) -> list[str]:
    """Flatten expected answers to compare with user inputs one-by-one."""
    exp = []
    for words in correct_items:
        for w in words:
            exp.append(normalize_text(w))
    return exp

def passage_ids_for_chapter(df: pd.DataFrame, chapter: str) -> list[int]:
    """Return 1..N passage numbers within the chapter."""
    sub = df[df["Chapter"] == chapter].copy()
    return list(range(1, len(sub) + 1))

@st.cache_data(show_spinner=False)
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)

    # Be tolerant about column naming
    # Required: Chapter, Passage, Correct answers
    col_map = {}
    for c in df.columns:
        cc = c.strip().lower()
        if cc == "chapter":
            col_map[c] = "Chapter"
        elif cc == "passage":
            col_map[c] = "Passage"
        elif cc in ("correct answers", "correct_answers", "answers", "correct answer"):
            col_map[c] = "Correct answers"

    df = df.rename(columns=col_map)

    required = {"Chapter", "Passage", "Correct answers"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")

    # Clean
    df["Chapter"] = df["Chapter"].astype(str).str.strip()
    df["Passage"] = df["Passage"].astype(str)
    df["Correct answers"] = df["Correct answers"].astype(str)

    # Keep stable order: Chapter then original row order
    df["_row"] = range(len(df))
    df = df.sort_values(["Chapter", "_row"], ignore_index=True).drop(columns=["_row"])
    return df


# =========================
# STATE
# =========================
def init_state():
    defaults = {
        "started": False,
        "start_time": None,
        "chapter": None,
        "passage_no": None,   # 1-based within chapter
        "row_idx": None,      # absolute row index in df
        "submitted": False,
        "attempts": 0,
        "last_results": None,  # list[bool]
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_quiz():
    for k in list(st.session_state.keys()):
        if k.startswith("ans_"):
            del st.session_state[k]
    st.session_state.started = False
    st.session_state.start_time = None
    st.session_state.chapter = None
    st.session_state.passage_no = None
    st.session_state.row_idx = None
    st.session_state.submitted = False
    st.session_state.attempts = 0
    st.session_state.last_results = None

init_state()


# =========================
# UI
# =========================
st.title("📘 Passage Blank Practice")
st.caption("Select a chapter and passage, click Start, then submit your answers. Feedback appears after submission.")

# Load data (with friendly error)
try:
    df = load_data(CSV_URL)
except Exception as e:
    st.error("Failed to load CSV. Check your RAW GitHub CSV URL and the required columns.")
    st.code(str(e))
    st.stop()

chapters = sorted(df["Chapter"].dropna().unique().tolist())
if not chapters:
    st.warning("No chapters found in the CSV.")
    st.stop()

# Controls
c1, c2, c3 = st.columns([2, 2, 2], vertical_alignment="center")

with c1:
    chapter = st.selectbox("Chapter", chapters, index=0, key="chapter_select")

# Passage number within selected chapter
sub_df = df[df["Chapter"] == chapter].reset_index(drop=False)  # keep original index in "index"
if sub_df.empty:
    st.warning("No passages found for this chapter.")
    st.stop()

passage_numbers = list(range(1, len(sub_df) + 1))
with c2:
    passage_no = st.selectbox("Passage number", passage_numbers, index=0, key="passage_select")

with c3:
    start_btn = st.button("✅ Start", use_container_width=True)
    reset_btn = st.button("🔄 Reset", use_container_width=True)

if reset_btn:
    reset_quiz()
    st.rerun()

# Start logic
if start_btn:
    st.session_state.started = True
    st.session_state.start_time = datetime.now()
    st.session_state.chapter = chapter
    st.session_state.passage_no = passage_no
    # Convert passage_no (1-based) to row in sub_df (0-based)
    row = sub_df.iloc[passage_no - 1]
    st.session_state.row_idx = int(row["index"])
    st.session_state.submitted = False
    st.session_state.last_results = None

    # Clear old answer inputs
    for k in list(st.session_state.keys()):
        if k.startswith("ans_"):
            del st.session_state[k]

# Show practice only after start
if not st.session_state.started or st.session_state.row_idx is None:
    st.info("Type your selections above and click **Start** to begin.")
    st.stop()

row = df.loc[st.session_state.row_idx]
correct_items = parse_correct_answers(row["Correct answers"])
expected = expected_flat_list(correct_items)

# Header + passage (markdown with HTML for consistent blanks)
st.markdown(f"## {row['Chapter']} · Passage {st.session_state.passage_no}")
passage_html = render_passage_with_numbered_blanks(row["Passage"], correct_items)

st.markdown(
    f"""
<div style="line-height:1.65; font-size:1.05rem;">
{passage_html}
</div>
<hr>
""",
    unsafe_allow_html=True,
)

st.markdown("### Your answers")

# Compact input UI:
# - Each numbered blank group shows a small row of text inputs
# - Uses columns so inputs do not become huge
with st.form("answer_form", clear_on_submit=False):
    ans_flat = []
    input_idx = 0

    for blank_no, words in enumerate(correct_items, start=1):
        n = max(1, len(words))

        # Label + input(s)
        label_col, inputs_col = st.columns([1, 5], vertical_alignment="center")
        label_col.markdown(f"**({blank_no})**")

        if n == 1:
            a, spacer = inputs_col.columns([1.6, 3.4])
            val = a.text_input(
                f"({blank_no})",
                key=f"ans_{input_idx}",
                label_visibility="collapsed",
                placeholder="type one word",
            )
            ans_flat.append(val)
            input_idx += 1
        else:
            # Multi-word: show (n)-1, (n)-2...
            # Put up to 4 inputs per row, then wrap
            remaining = n
            j = 1
            while remaining > 0:
                k = min(4, remaining)
                cols = inputs_col.columns([1.2] * k + [3.0])  # last is spacer
                for i in range(k):
                    val = cols[i].text_input(
                        f"({blank_no})-{j}",
                        key=f"ans_{input_idx}",
                        label_visibility="collapsed",
                        placeholder=f"word {j}",
                    )
                    ans_flat.append(val)
                    input_idx += 1
                    j += 1
                remaining -= k

    submit = st.form_submit_button("📌 Submit", use_container_width=True)

if submit:
    st.session_state.attempts += 1
    user_norm = [normalize_text(a) for a in ans_flat]

    # Compare one-by-one
    results = []
    for u, e in zip(user_norm, expected):
        results.append(u == e)

    st.session_state.submitted = True
    st.session_state.last_results = results
    st.session_state.finish_time = datetime.now()

# Feedback
if st.session_state.submitted and st.session_state.last_results is not None:
    results = st.session_state.last_results
    total = len(results)
    correct_n = sum(results)

    if correct_n == total:
        st.success(f"✅ Perfect! {correct_n} / {total}")
    else:
        st.warning(f"📌 Result: {correct_n} / {total}")

    # Show per-blank feedback matching (1)(2)(3)...
    st.markdown("#### Feedback by blank")
    flat_idx = 0
    for blank_no, words in enumerate(correct_items, start=1):
        n = max(1, len(words))
        group_ok = all(results[flat_idx:flat_idx + n])
        status = "✅ Correct" if group_ok else "❌ Incorrect"
        st.write(f"({blank_no}) {status}")
        flat_idx += n

    # Incorrect list (show expected answers for teacher view)
    wrong_items = []
    for i, ok in enumerate(results, start=1):
        if not ok:
            wrong_items.append(i)

    if wrong_items:
        with st.expander("Show correct answers (for checking)"):
            # Reconstruct answer groups
            for blank_no, words in enumerate(correct_items, start=1):
                st.write(f"({blank_no}) " + " ".join(words))

    # Simple time info
    start_t = st.session_state.start_time
    end_t = st.session_state.finish_time
    if start_t and end_t:
        st.caption(f"Started: {start_t.strftime('%Y-%m-%d %H:%M:%S')}  |  Completed: {end_t.strftime('%Y-%m-%d %H:%M:%S')}")
        st.caption(f"Trials (submissions): {st.session_state.attempts}")
