import re
import unicodedata
import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="Speech Organs Quiz", page_icon="🗣️", layout="wide")
st.title("🗣️ Speech Organs — Image Quiz")

# ---------------- Config ----------------
IMAGE_URL = "https://raw.githubusercontent.com/MK316/english-phonetics/main/pages/images/vocal_organ.png"
TOTAL_ITEMS = 14

# ANSWER_KEY: map number -> list of accepted answers/synonyms (all lowercase here).
# 💡 Edit these to match your exact diagram labels.
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
    """Lowercase, remove accents & non-letters, collapse spaces/hyphens."""
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = re.sub(r"[\-_/]", " ", s)       # treat -, _, / as spaces
    s = re.sub(r"[^a-z\s]", "", s)      # letters & spaces only
    s = re.sub(r"\s+", " ", s).strip()  # collapse spaces
    return s

def is_correct(num: int, user_text: str) -> bool:
    if not user_text:
        return False
    gold = [normalize(x) for x in ANSWER_KEY.get(num, [])]
    guess = normalize(user_text)
    # exact among normalized synonyms
    if guess in gold:
        return True
    # small extra: allow plural 's' mismatch (e.g., "vocal cord(s)")
    if guess.endswith("s") and guess[:-1] in gold:
        return True
    if (guess + "s") in gold:
        return True
    return False

# ---------------- Tabs ----------------
tab1, tab2, tab3 = st.tabs(["Quiz", "Tab 2 (coming soon)", "Tab 3 (coming soon)"])

# =========================================================
# TAB 1 — Image + 14-question short-answer quiz
# =========================================================
with tab1:
    # Center the image
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(IMAGE_URL, use_container_width=True, caption="Refer to the numbers (1–14) on this diagram.")

    # --------- per-session state (isolated per user) ---------
    if "quiz_current" not in st.session_state:
        st.session_state.quiz_current = 1                # which number we're asking now
    if "quiz_answers" not in st.session_state:
        st.session_state.quiz_answers = {}               # number -> user's raw answer
    if "quiz_done" not in st.session_state:
        st.session_state.quiz_done = False

    # Reset button
    reset_cols = st.columns([1, 6, 1])
    with reset_cols[0]:
        if st.button("🔄 Reset quiz", use_container_width=True):
            st.session_state.quiz_current = 1
            st.session_state.quiz_answers = {}
            st.session_state.quiz_done = False
            st.rerun()

    st.divider()

    # --------- Quiz flow ---------
    if not st.session_state.quiz_done:
        num = st.session_state.quiz_current
        st.subheader(f"Question {num} of {TOTAL_ITEMS}")
        st.write(f"**Write the name of the speech organ for the number {num}.**")

        # Use a unique key per question so the input clears when advancing
        ans_key = f"answer_q{num}"
        with st.form(key=f"form_q{num}", clear_on_submit=True):
            user_input = st.text_input("Your answer:", key=ans_key, placeholder="Type here…")
            submitted = st.form_submit_button("Submit", use_container_width=True)

        if submitted:
            st.session_state.quiz_answers[num] = user_input
            if num < TOTAL_ITEMS:
                st.session_state.quiz_current = num + 1
                st.rerun()
            else:
                st.session_state.quiz_done = True
                st.rerun()

    # --------- Results ---------
    else:
        st.subheader("Results")
        # Build a small table of correctness
        rows = []
        correct_count = 0
        for n in range(1, TOTAL_ITEMS + 1):
            user = st.session_state.quiz_answers.get(n, "")
            ok = is_correct(n, user)
            correct_count += 1 if ok else 0
            gold_display = ", ".join(ANSWER_KEY.get(n, [])) or "(set me in ANSWER_KEY)"
            rows.append({
                "No.": n,
                "Your answer": user if user else "—",
                "Correct answers (accepted)": gold_display,
                "Result": "✅ Correct" if ok else "❌ Incorrect",
            })

        st.success(f"Score: **{correct_count} / {TOTAL_ITEMS}**")
        st.dataframe(rows, use_container_width=True, hide_index=True)

        # Retake
        if st.button("🧪 Retake quiz", use_container_width=True):
            st.session_state.quiz_current = 1
            st.session_state.quiz_answers = {}
            st.session_state.quiz_done = False
            st.experimental_rerun()

# =========================================================
# TAB 2 — placeholder
# =========================================================
with tab2:
    st.info("Tab 2 will be updated later.")

# =========================================================
# TAB 3 — placeholder
# =========================================================
with tab3:
    st.info("Tab 3 will be updated later.")
