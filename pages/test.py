import re
import pandas as pd
import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Passage Fill-in Quiz", layout="wide")

# =========================
# 1) Data load
# =========================
SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/1QYiGg1ME8pql-wAnwGsU6GjTc6bniKHvsVJK4aMn3fI/edit?usp=sharing"

@st.cache_data(show_spinner=False)
def load_sheet(url: str) -> pd.DataFrame:
    df = pd.read_csv(url)

    # Expected columns (case-sensitive). Rename if your sheet differs.
    # Chapter | Passage | Correct answers
    required = {"Chapter", "Passage", "Correct answers"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in sheet: {missing}")

    df = df.dropna(subset=["Chapter", "Passage", "Correct answers"]).copy()
    df["Chapter"] = df["Chapter"].astype(str).str.strip()
    df["Passage"] = df["Passage"].astype(str)
    df["Correct answers"] = df["Correct answers"].astype(str)

    return df

def normalize(s: str) -> str:
    """Normalize user input and answers for robust matching."""
    return re.sub(r"\s+", " ", str(s).strip().lower())

def split_answers(ans: str):
    """Split comma-separated answers into a list."""
    return [a.strip() for a in str(ans).split(",") if a.strip()]

def count_blanks(passage: str) -> int:
    """Count occurrences of ___ in the passage."""
    return len(re.findall(r"___", passage))

# =========================
# 2) UI + session state
# =========================
st.title("🧩 Passage Fill-in Practice")
st.caption("Select a chapter and passage, click Start, fill the blanks, then Submit.")

try:
    df = load_sheet(SHEET_CSV_URL)
except Exception as e:
    st.error(f"Failed to load Google Sheet.\n\n{e}")
    st.stop()

chapters = sorted(df["Chapter"].unique().tolist())
left, right = st.columns([1, 2], vertical_alignment="top")

with left:
    chapter = st.selectbox("Chapter", chapters, key="sel_chapter")

    df_ch = df[df["Chapter"] == chapter].reset_index(drop=True)
    passage_idx = st.selectbox(
        "Passage number",
        options=list(range(1, len(df_ch) + 1)),
        format_func=lambda x: f"Passage {x}",
        key="sel_passage_num",
    )

    # Reset button
    if st.button("Reset", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k.startswith(("quiz_", "blank_", "fb_")):
                del st.session_state[k]
        st.rerun()

# Identify selected row
row = df_ch.iloc[int(passage_idx) - 1]
passage_text = row["Passage"]
answers = split_answers(row["Correct answers"])

n_blanks = count_blanks(passage_text)

# Safety check: number of blanks vs answers
if n_blanks != len(answers):
    st.warning(
        f"⚠️ This passage has {n_blanks} blank(s) but {len(answers)} answer(s). "
        f"Please make them match in the Google Sheet."
    )

# Session keys
quiz_key = f"quiz_{chapter}_{passage_idx}"

if quiz_key not in st.session_state:
    st.session_state[quiz_key] = {
        "started": False,
        "submitted": False,
        "start_time": None,
        "submit_time": None,
    }

# =========================
# 3) Start / render passage
# =========================
with right:
    st.markdown("#### Passage")

    # Start button
    c1, c2 = st.columns([1, 3])
    with c1:
        start_clicked = st.button("✅ Start", use_container_width=True)

    if start_clicked and not st.session_state[quiz_key]["started"]:
        st.session_state[quiz_key]["started"] = True
        st.session_state[quiz_key]["submitted"] = False
        st.session_state[quiz_key]["start_time"] = datetime.now().isoformat(timespec="seconds")

        # Clear prior blank inputs for this passage
        for i in range(n_blanks):
            k = f"blank_{chapter}_{passage_idx}_{i}"
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()

    if not st.session_state[quiz_key]["started"]:
        st.info("Click **Start** to begin.")
        st.stop()

    # Build "in-place" passage renderer:
    parts = re.split(r"___", passage_text)

    # Render each blank as a small text input between text chunks
    # We use columns so the blank appears "in the flow" (not perfect inline HTML,
    # but visually it sits between text segments).
    for i in range(n_blanks):
        st.write(parts[i], end="") if hasattr(st, "write") else None  # harmless fallback

        # Put blank next to text using columns (compact)
        col_text, col_blank = st.columns([8, 2], vertical_alignment="center")
        with col_text:
            st.markdown(parts[i])
        with col_blank:
            st.text_input(
                label=f"Blank {i+1}",
                key=f"blank_{chapter}_{passage_idx}_{i}",
                label_visibility="collapsed",
                placeholder="type here",
            )

    # Last chunk after final blank
    if parts:
        st.markdown(parts[-1])

    st.markdown("---")

    # Submission button (only after all blanks have something)
    user_inputs = [
        st.session_state.get(f"blank_{chapter}_{passage_idx}_{i}", "")
        for i in range(n_blanks)
    ]
    all_filled = all(normalize(x) for x in user_inputs)

    submit_disabled = (not all_filled) or st.session_state[quiz_key]["submitted"]

    submit_clicked = st.button(
        "📌 Submit",
        use_container_width=True,
        disabled=submit_disabled,
    )

    if not all_filled and not st.session_state[quiz_key]["submitted"]:
        st.caption("Fill in all blanks to enable Submit.")

    # =========================
    # 4) Feedback
    # =========================
    if submit_clicked and not st.session_state[quiz_key]["submitted"]:
        st.session_state[quiz_key]["submitted"] = True
        st.session_state[quiz_key]["submit_time"] = datetime.now().isoformat(timespec="seconds")

        # Compare
        results = []
        correct_count = 0

        for i in range(n_blanks):
            ui = normalize(user_inputs[i])
            ca = normalize(answers[i]) if i < len(answers) else ""
            ok = (ui == ca)
            results.append((user_inputs[i], answers[i] if i < len(answers) else "", ok))
            correct_count += int(ok)

        st.session_state[f"fb_{quiz_key}"] = {
            "results": results,
            "correct_count": correct_count,
            "total": n_blanks,
        }
        st.rerun()

    fb = st.session_state.get(f"fb_{quiz_key}", None)
    if fb and st.session_state[quiz_key]["submitted"]:
        total = fb["total"]
        correct_count = fb["correct_count"]
        results = fb["results"]

        st.subheader("Feedback")

        # Overall
        if total > 0 and correct_count == total:
            st.success(f"✅ Perfect! {correct_count} / {total}")
        else:
            st.warning(f"Result: {correct_count} / {total}")

        # Per blank
        for i, (u, a, ok) in enumerate(results, start=1):
            if ok:
                st.success(f"Blank {i}: Correct ✅  ({u})")
            else:
                st.error(f"Blank {i}: Incorrect ❌  (Your answer: {u} | Correct: {a})")

        st.caption(
            f"Start time: {st.session_state[quiz_key]['start_time']}  |  "
            f"Submit time: {st.session_state[quiz_key]['submit_time']}"
        )
