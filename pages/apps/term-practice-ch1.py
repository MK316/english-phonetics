import streamlit as st
import pandas as pd
import random
from gtts import gTTS
from io import BytesIO

# Load data
sheet_url = "https://raw.githubusercontent.com/MK316/classmaterial/main/Phonetics/ch01_glossary.csv"
df = pd.read_csv(sheet_url)

# App title
st.title("🧠 Term Practice App")

# Initialize session state
if "selected_row" not in st.session_state:
    st.session_state.selected_row = None
if "show_meaning" not in st.session_state:
    st.session_state.show_meaning = False
if "selected_term" not in st.session_state:
    st.session_state.selected_term = None
if "quiz_index" not in st.session_state:
    st.session_state.quiz_index = 0
if "term_list" not in st.session_state:
    st.session_state.term_list = df.sample(frac=1).reset_index(drop=True)  # shuffled list for quiz
if "score" not in st.session_state:
    st.session_state.score = 0

# Create tabs
tab1, tab2, tab3 = st.tabs(["📘 Term List", "🎲 Random Practice", "📝 Quiz Mode"])

# Tab 1: Show the full term list
with tab1:
    st.subheader("📘 Full Glossary")
    st.dataframe(df)

# Tab 2: Random Practice
with tab2:
    st.subheader("🎲 Practice a Random Term")

    def pick_random_term():
        st.session_state.selected_row = df.sample(1).iloc[0]
        st.session_state.show_meaning = False

    st.button("🎯 Pick a Random Term", on_click=pick_random_term)

    if st.session_state.selected_row is not None:
        row = st.session_state.selected_row
        st.markdown(f"### Hint: {row['Hint']}")

        if st.button("Show Meaning"):
            st.session_state.show_meaning = True

        if st.session_state.show_meaning:
            st.markdown(f"**Term:** {row['Term']}")
            st.markdown(f"**Meaning:** {row['Description']}")

# Tab 3: Audio Description → Term Guess (Quiz Mode)
with tab3:
    st.subheader("🔊 Audio Quiz: Guess the Term")

    def get_next_quiz_term():
        st.session_state.selected_term = st.session_state.term_list.iloc[st.session_state.quiz_index]

    if st.button("🔁 Next"):
        if st.session_state.quiz_index < len(st.session_state.term_list):
            get_next_quiz_term()
            st.session_state.quiz_index += 1
        else:
            st.warning("🎉 You've completed the quiz!")
            st.session_state.quiz_index = 0
            st.session_state.score = 0
            st.session_state.term_list = df.sample(frac=1).reset_index(drop=True)

    if st.session_state.selected_term is not None:
        text = st.session_state.selected_term["Description"]
        tts = gTTS(text)
        mp3_fp = BytesIO()
        tts.write_to_fp(mp3_fp)
        st.audio(mp3_fp.getvalue(), format="audio/mp3")

        answer = st.text_input("Your Answer:")
        if answer:
            correct = st.session_state.selected_term["Term"].strip().lower()
            if answer.strip().lower() == correct:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error(f"❌ Incorrect. The correct answer was: {correct}")

    st.markdown(f"**Score:** {st.session_state.score}")
