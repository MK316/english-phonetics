import streamlit as st
import pandas as pd
from datetime import datetime
import re

st.set_page_config(page_title="Passage Blanks Practice", layout="wide")
st.title("🧩 Passage Blank Practice (10-underscore blanks)")

# ✅ CHANGE THIS to your GitHub RAW CSV URL
CSV_URL = "https://raw.githubusercontent.com/MK316/english-phonetics/refs/heads/main/pages/readings/readingquiz001a.csv"
# Expected columns: Chapter, Passage, Correct answers
# Passage uses ___ for each blank location
# Correct answers are comma-separated, e.g. "Phonetics, intelligibly, described"
# If an answer is multi-word, e.g. "in fact", we'll create two blanks for that single item.

@st.cache_data
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]
    required = {"Chapter", "Passage", "Correct answers"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing columns: {', '.join(sorted(missing))}")
    df["Chapter"] = df["Chapter"].astype(str).str.strip()
    df["Passage"] = df["Passage"].astype(str)
    df["Correct answers"] = df["Correct answers"].astype(str)
    return df

def parse_correct_answers(ans_cell: str) -> list[list[str]]:
    """
    Returns list of items, where each item is list of words for that blank.
    Example: "in fact, phonetics" -> [["in","fact"], ["phonetics"]]
    """
    items = [a.strip() for a in ans_cell.split(",") if a.strip()]
    out = []
    for item in items:
        # split on whitespace; keep alphabet+apostrophe; minimal cleanup
        words = re.findall(r"[A-Za-z']+", item)
        if not words:
            words = item.split()
        out.append([w.strip() for w in words if w.strip()])
    return out

def render_passage_with_blanks(passage: str, correct_items: list[list[str]]) -> str:
    """
    Replaces each ___ in passage with underscores.
    If correct item has N words, render N blanks separated by spaces.
    """
    blank_tokens = []
    for words in correct_items:
        n = max(1, len(words))
        blank_tokens.append(" ".join(["__________"] * n))

    # replace ___ sequentially
    result = passage
    for token in blank_tokens:
        if "___" in result:
            result = result.replace("___", token, 1)
        else:
            break
    return result

def init_session_keys(total_inputs: int):
    if "started" not in st.session_state:
        st.session_state.started = False
    if "started_at" not in st.session_state:
        st.session_state.started_at = None
    if "submitted" not in st.session_state:
        st.session_state.submitted = False
    if "attempts" not in st.session_state:
        st.session_state.attempts = 0
    if "last_result" not in st.session_state:
        st.session_state.last_result = None

    # ensure input boxes exist
    for i in range(total_inputs):
        k = f"ans_{i}"
        if k not in st.session_state:
            st.session_state[k] = ""

def do_start():
    st.session_state.started = True
    st.session_state.submitted = False
    st.session_state.attempts = 0
    st.session_state.last_result = None
    st.session_state.started_at = datetime.now()

def do_reset(total_inputs: int):
    st.session_state.started = False
    st.session_state.submitted = False
    st.session_state.attempts = 0
    st.session_state.last_result = None
    st.session_state.started_at = None
    for i in range(total_inputs):
        k = f"ans_{i}"
        if k in st.session_state:
            st.session_state[k] = ""

# -------------------------
# Load data
# -------------------------
try:
    df = load_data(CSV_URL)
except Exception as e:
    st.error("Failed to load CSV.")
    st.code(str(e))
    st.stop()

chapters = sorted(df["Chapter"].dropna().unique().tolist())
c1, c2, c3 = st.columns([2, 2, 2])
with c1:
    user_name = st.text_input("Your name (English):", key="user_name")
with c2:
    selected_ch = st.selectbox("Select Chapter:", chapters, key="selected_chapter")

filtered = df[df["Chapter"] == selected_ch].reset_index(drop=True)

with c3:
    passage_idx = st.selectbox(
        "Select Passage number:",
        list(range(1, len(filtered) + 1)),
        key="passage_number",
    )

row = filtered.iloc[passage_idx - 1]
passage_text = row["Passage"]
correct_items = parse_correct_answers(row["Correct answers"])  # list[list[str]]

# Flatten expected words for input matching
expected_words = [w for item in correct_items for w in item]
total_inputs = len(expected_words)

init_session_keys(total_inputs)

st.caption("Click Start. Read the passage (blanks shown as __________). Then type answers below and submit.")

b1, b2 = st.columns([1, 1])
with b1:
    st.button("✅ Start", on_click=do_start, use_container_width=True)
with b2:
    st.button("🔄 Reset", on_click=lambda: do_reset(total_inputs), use_container_width=True)

st.divider()

if not st.session_state.started:
    st.info("Click **Start** to begin.")
    st.stop()

# -------------------------
# Show full passage (NOT broken)
# -------------------------
display_passage = render_passage_with_blanks(passage_text, correct_items)

st.subheader(f"{selected_ch} · Passage {passage_idx}")
st.write(display_passage)

st.divider()

# -------------------------
# Inputs (all together BELOW passage)
# -------------------------
st.markdown("### Your answers")

# Show grouped inputs per item (so multi-word answers appear as 2 blanks)
input_idx = 0
for item_i, words in enumerate(correct_items, start=1):
    n = max(1, len(words))
    cols = st.columns(min(3, n)) if n > 1 else [st]
    if n == 1:
        st.text_input(f"Blank {item_i}", key=f"ans_{input_idx}")
    else:
        # If more than 3 words (rare), we still render in rows
        st.markdown(f"**Blank {item_i}** (multi-word)")
        for j in range(n):
            # make rows of up to 3 inputs
            if j % 3 == 0:
                cols = st.columns(min(3, n - j))
            cols[j % 3].text_input(f"Word {j+1}", key=f"ans_{input_idx}")
            input_idx += 1
        continue
    input_idx += 1

st.divider()

def do_submit():
    st.session_state.submitted = True
    st.session_state.attempts += 1

    user_words = [(st.session_state.get(f"ans_{i}", "") or "").strip() for i in range(total_inputs)]

    # per-word correctness (case-insensitive)
    per_word = []
    score = 0
    for i, (uw, ew) in enumerate(zip(user_words, expected_words), start=1):
        ok = (uw.lower() == ew.lower()) and ew.strip() != ""
        per_word.append({"index": i, "user": uw, "correct": ew, "ok": ok})
        if ok:
            score += 1

    st.session_state.last_result = {
        "score": score,
        "total": total_inputs,
        "per_word": per_word,
        "finished_at": datetime.now(),
    }

st.button("📩 Submit (check answers)", on_click=do_submit, use_container_width=True)

# -------------------------
# Feedback (after submission)
# -------------------------
if st.session_state.submitted and st.session_state.last_result:
    res = st.session_state.last_result

    st.subheader("Feedback")
    incorrect = [x for x in res["per_word"] if not x["ok"]]

    if not incorrect:
        st.success("All correct ✅")
    else:
        st.warning(f"Incorrect words: {len(incorrect)}")
        for x in incorrect:
            st.error(f"Word {x['index']}: your answer = '{x['user']}'  |  correct = '{x['correct']}'")
