import re
import unicodedata
import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="Vocal Organs Quiz", page_icon="🗣️", layout="wide")
st.markdown("#### 🗣️ Understanding Speech Production")

# ---------------- Image + Answer Key ----------------
IMAGE_URL = "https://raw.githubusercontent.com/MK316/english-phonetics/main/pages/images/vocal_organ.png"
TOTAL_ITEMS = 14

ANSWER_KEY = {
    1:  ["upper lip"],
    2:  ["upper teeth"],
    3:  ["alveolar ridge"],
    4:  ["hard palate"],
    5:  ["soft palate", "velum"],
    6:  ["uvula"],
    7:  ["epiglottis"],
    8:  ["lower lip"],
    9:  ["tongue tip", "tip of the tongue"],
    10: ["tongue blade", "blade of the tongue"],
    11: ["front of the tongue", "tongue front"],
    12: ["center of the tongue", "tongue center"],
    13: ["back of the tongue", "tongue back"],
    14: ["tongue root", "root of the tongue"],
}

# ---------------- Helpers ----------------
def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = re.sub(r"[\-_/]", " ", s)
    s = re.sub(r"[^a-z\s]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def is_correct(num: int, user_text: str) -> bool:
    if not user_text:
        return False
    gold = [normalize(x) for x in ANSWER_KEY.get(num, [])]
    guess = normalize(user_text)
    return guess in gold or (guess.endswith("s") and guess[:-1] in gold) or ((guess + "s") in gold)

# ---------------- Main App UI ----------------
st.image(IMAGE_URL, use_container_width=True,
         caption="Refer to the numbers (1–14) on this diagram.")

if "answers" not in st.session_state:
    st.session_state.answers = {i: "" for i in range(1, TOTAL_ITEMS + 1)}
if "checked" not in st.session_state:
    st.session_state.checked = False
if "results" not in st.session_state:
    st.session_state.results = {}

top = st.columns([1, 6, 1])
with top[0]:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.answers = {i: "" for i in range(1, TOTAL_ITEMS + 1)}
        st.session_state.checked = False
        st.session_state.results = {}
        st.rerun()

st.divider()
st.subheader("📌 Type all answers, then click the button below to check the answers.")

with st.form("quiz_form"):
    col_left, col_right = st.columns(2)
    for i in range(1, TOTAL_ITEMS + 1, 2):
        with col_left:
            st.session_state.answers[i] = st.text_input(
                f"{i}. ❄️ Number {i}",
                value=st.session_state.answers.get(i, ""),
                key=f"ans_{i}"
            )
        j = i + 1
        if j <= TOTAL_ITEMS:
            with col_right:
                st.session_state.answers[j] = st.text_input(
                    f"{j}. ❄️ Number {j}",
                    value=st.session_state.answers.get(j, ""),
                    key=f"ans_{j}"
                )
    submitted = st.form_submit_button("Check answers", use_container_width=True)

if submitted:
    st.session_state.results = {
        n: is_correct(n, st.session_state.answers.get(n, "")) for n in range(1, TOTAL_ITEMS + 1)
    }
    st.session_state.checked = True
    st.rerun()

if st.session_state.checked:
    correct_count = sum(1 for ok in st.session_state.results.values() if ok)
    st.success(f"Score: **{correct_count} / {TOTAL_ITEMS}**")
    rows = []
    for n in range(1, TOTAL_ITEMS + 1):
        user = st.session_state.answers.get(n, "")
        ok = st.session_state.results.get(n, False)
        gold_display = ", ".join(ANSWER_KEY.get(n, [])) or "(not defined)"
        rows.append({
            "No.": n,
            "Your answer": user if user else "—",
            "Accepted answers": gold_display,
            "Result": "✅ Correct" if ok else "❌ Incorrect",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    if st.button("🧪 Try again", use_container_width=True):
        st.session_state.checked = False
        st.session_state.results = {}
        st.rerun()
