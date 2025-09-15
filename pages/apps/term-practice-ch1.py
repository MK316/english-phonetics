import streamlit as st

from term_helpers import df, tts_bytes, answer_prompt, hint_from_term, build_report_bytes

st.set_page_config(page_title="Term Practice Activities", layout="wide")
st.title("🧠 Phonetics Term Practice")

# Tabs: Text practice, Audio practice, Audio quiz
tab1, tab2, tab3 = st.tabs([
    "✍️ Text Practice", "🔊 Audio Practice", "🧪 Audio Quiz (PDF report)"
])

# ---------------- Tab 1 ----------------
with tab1:
    st.subheader("✍️ Practice Terms with Text Descriptions")
    HINT_UNDERSCORES = 4
    num_items = st.number_input("How many terms to practice?", min_value=1, max_value=len(df), value=3, key="text_input")

    if "text_items" not in st.session_state or st.button("🔄 New Practice", key="new_text"):
        st.session_state.text_items = df.sample(num_items).reset_index(drop=True)
        st.session_state.text_answers = [""] * num_items

    for i, row in st.session_state.text_items.iterrows():
        desc = str(row["Description"]).strip()
        term = str(row["Term"]).strip()
        st.markdown(f"**{i+1}. {desc}**")
        hint = hint_from_term(term, underscores=HINT_UNDERSCORES)
        st.markdown(f"<div style='opacity:0.8; margin-top:-0.25rem;'>Hint: <code>{hint}</code></div>", unsafe_allow_html=True)
        st.write(answer_prompt(row))
        st.session_state.text_answers[i] = st.text_input(
            f"Your answer {i+1}", value=st.session_state.text_answers[i], key=f"text_answer_{i}"
        )

    if st.button("✅ Check Answers", key="check_text"):
        score = 0
        for i, row in st.session_state.text_items.iterrows():
            gold = " ".join(str(row["Term"]).strip().lower().split())
            guess = " ".join(str(st.session_state.text_answers[i]).strip().lower().split())
            if guess == gold:
                score += 1
                st.success(f"{i+1}. Correct!")
            else:
                st.error(f"{i+1}. Incorrect. ✅ Correct: {row['Term']}")
        st.success(f"Your score: {score} / {len(st.session_state.text_items)}")
        if score == len(st.session_state.text_items):
            st.balloons()

# ---------------- Tab 2 ----------------
with tab2:
    st.subheader("🔊 Practice Terms with Audio")
    num_items_audio = st.number_input("How many terms?", min_value=1, max_value=len(df), value=3, key="audio_num")

    if "audio_idx" not in st.session_state:
        st.session_state.audio_idx = []
    if "audio_answers" not in st.session_state:
        st.session_state.audio_answers = []

    if st.button("🔄 Generate Practice (Audio)", key="new_audio"):
        sample = df.sample(int(num_items_audio), random_state=None)
        st.session_state.audio_idx = sample.index.tolist()
        st.session_state.audio_answers = [""] * len(st.session_state.audio_idx)
        st.rerun()

    if not st.session_state.audio_idx:
        st.info("Set the number above and click Generate Practice to start.")
    else:
        for i, idx in enumerate(st.session_state.audio_idx):
            row = df.loc[idx]
            term = str(row["Term"]).strip()
            desc = str(row["Description"]).strip()
            st.markdown(f"**{i+1}. Listen to the definition and type the term**")
            st.audio(tts_bytes(desc), format="audio/mp3")
            st.write(answer_prompt(row))
            st.session_state.audio_answers[i] = st.text_input(
                f"Your answer {i+1}", value=st.session_state.audio_answers[i], key=f"audio_answer_{idx}"
            )

        if st.button("✅ Check Answers (Audio)", key="check_audio"):
            score = 0
            for i, idx in enumerate(st.session_state.audio_idx):
                row = df.loc[idx]
                gold = " ".join(str(row["Term"]).strip().lower().split())
                guess = " ".join(str(st.session_state.audio_answers[i]).strip().lower().split())
                if guess == gold:
                    score += 1
                    st.success(f"{i+1}. Correct!")
                else:
                    st.error(f"{i+1}. Incorrect. ✅ Correct: {row['Term']}")
            st.success(f"Your score: {score} / {len(st.session_state.audio_idx)}")
            if score == len(st.session_state.audio_idx):
                st.balloons()

# ---------------- Tab 3 ----------------
with tab3:
    st.subheader("🧪 Audio Quiz with PDF Report")
    name_col, btn_col = st.columns([2, 1])
    with name_col:
        typed_name = st.text_input("Enter your name", key="tab3_user")
    with btn_col:
        start_clicked = st.button("Start Quiz ▶️", use_container_width=True, key="tab3_start")

    if "tab3_started" not in st.session_state:
        st.session_state.tab3_started = False
        st.session_state.tab3_idx = 0
        st.session_state.tab3_order = []
        st.session_state.tab3_answers = []
        st.session_state.tab3_done = False

    if start_clicked and typed_name.strip():
        st.session_state.tab3_started = True
        st.session_state.tab3_order = df.sample(frac=1).index.tolist()
        st.session_state.tab3_idx = 0
        st.session_state.tab3_answers = [""] * len(st.session_state.tab3_order)
        st.session_state.tab3_user = typed_name.strip()
        st.rerun()

    if st.session_state.tab3_started and not st.session_state.tab3_done:
        idx = st.session_state.tab3_idx
        row = df.loc[st.session_state.tab3_order[idx]]
        st.info(f"Question {idx+1} of {len(st.session_state.tab3_order)}")
        st.audio(tts_bytes(row["Description"]), format="audio/mp3")
        st.write(answer_prompt(row))
        st.session_state.tab3_answers[idx] = st.text_input("Your answer", value=st.session_state.tab3_answers[idx])

        if st.button("Submit & Next ➡️"):
            if idx < len(st.session_state.tab3_order) - 1:
                st.session_state.tab3_idx += 1
                st.rerun()
            else:
                st.session_state.tab3_done = True
                st.rerun()

    if st.session_state.tab3_done:
        total = len(st.session_state.tab3_order)
        score = 0
        wrong_items = []
        for i, idx in enumerate(st.session_state.tab3_order):
            row = df.loc[idx]
            gold = " ".join(str(row["Term"]).strip().lower().split())
            guess = " ".join(str(st.session_state.tab3_answers[i]).strip().lower().split())
            if guess == gold:
                score += 1
            else:
                wrong_items.append({
                    "term": row["Term"],
                    "description": row["Description"],
                    "your_answer": st.session_state.tab3_answers[i]
                })

        st.success(f"✅ Finished! Score: {score} / {total}")
        fname, mime, data = build_report_bytes(st.session_state.tab3_user, score, total, wrong_items)
        st.download_button("📄 Download PDF Report", data=data, file_name=fname, mime=mime)

        if wrong_items:
            st.write("Incorrect Items:")
            for item in wrong_items:
                st.markdown(f"- **{item['term']}** — {item['description']}  \n  _Your answer:_ {item['your_answer'] or '—'}")

        if st.button("🔁 Take Again"):
            st.session_state.tab3_started = False
            st.session_state.tab3_done = False
            st.rerun()
