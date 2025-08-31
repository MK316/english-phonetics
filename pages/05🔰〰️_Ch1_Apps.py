import re
import unicodedata
import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="Speech Organs Quiz", page_icon="🗣️", layout="wide")
st.title("🗣️ Speech Organs — Image Quiz")

# ---------------- Config ----------------
IMAGE_URL = "https://raw.githubusercontent.com/MK316/english-phonetics/main/pages/images/vocal_organ.png"
TOTAL_ITEMS = 14

# 👉 Edit to match your diagram labels (lowercase; include synonyms).
ANSWER_KEY = {
    1:  ["upper lip", "lip"],
    2:  ["upper teeth", "teeth"],
    3:  ["alveolar ridge", "alveolar"],
    4:  ["hard palate", "palate"],
    5:  ["soft palate", "velum"],
    6:  ["uvula"],
    7:  ["pharynx", "pharyngeal wall"],
    8:  ["epiglottis"],
    9:  ["glottis", "vocal folds", "vocal cords"],
    10: ["tongue tip", "apex"],
    11: ["tongue blade", "blade"],
    12: ["tongue front", "front of tongue"],
    13: ["tongue back", "dorsum", "back of tongue"],
    14: ["larynx", "voice box"],
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
    if guess in gold:
        return True
    if guess.endswith("s") and guess[:-1] in gold:
        return True
    if (guess + "s") in gold:
        return True
    return False

# ---------------- Tabs ----------------
tab1, tab2, tab3 = st.tabs(["Quiz", "Tab 2 (coming soon)", "Tab 3 (coming soon)"])

# =========================================================
# TAB 1 — Image + 14 text boxes + single "Check answers"
# =========================================================
with tab1:
    # Center the image
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(IMAGE_URL, use_container_width=True,
                 caption="Refer to the numbers (1–14) on this diagram.")

    # Per-session state (isolated per user)
    if "answers" not in st.session_state:
        st.session_state.answers = {i: "" for i in range(1, TOTAL_ITEMS + 1)}
    if "checked" not in st.session_state:
        st.session_state.checked = False
    if "results" not in st.session_state:
        st.session_state.results = {}

    # Reset
    top = st.columns([1, 6, 1])
    with top[0]:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.answers = {i: "" for i in range(1, TOTAL_ITEMS + 1)}
            st.session_state.checked = False
            st.session_state.results = {}
            st.rerun()

    st.divider()

    # ---- Input form with 14 boxes (two columns), each with question number label ----
    st.subheader("Type all answers, then click **Check answers**")
    with st.form("quiz_form"):
        col_left, col_right = st.columns(2)

        for i in range(1, TOTAL_ITEMS + 1, 2):
            # Left column: odd numbers
            with col_left:
                label_i = f"{i}. Write the name for the number {i}"
                st.session_state.answers[i] = st.text_input(
                    label_i,
                    value=st.session_state.answers.get(i, ""),
                    key=f"ans_{i}",
                    placeholder="Type here…",
                    label_visibility="visible",
                )
            # Right column: even numbers
            j = i + 1
            if j <= TOTAL_ITEMS:
                with col_right:
                    label_j = f"{j}. Write the name of the speech organ for the number {j}"
                    st.session_state.answers[j] = st.text_input(
                        label_j,
                        value=st.session_state.answers.get(j, ""),
                        key=f"ans_{j}",
                        placeholder="Type here…",
                        label_visibility="visible",
                    )

        submitted = st.form_submit_button("Check answers", use_container_width=True)

    # ---- Evaluate & show results ----
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
            gold_display = ", ".join(ANSWER_KEY.get(n, [])) or "(set me in ANSWER_KEY)"
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

# =========================================================
with tab2:
    st.info("Tab 2 will be updated later.")

with tab3:
    st.info("Tab 3 will be updated later.")
